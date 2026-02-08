// Background Service Worker
console.log('Background Service Worker Loaded');

// Helper to get state
async function getCrawlState() {
    const data = await chrome.storage.local.get('crawlState');
    return data.crawlState || {
        isCrawling: false,
        visited: [], // Set is not serializable, use Array
        queue: [],
        results: [],
        domain: '',
        maxPages: 200,
        crawlerTabId: null
    };
}

// Helper to save state
async function saveCrawlState(state) {
    await chrome.storage.local.set({ crawlState: state });
}

// Listen for messages from Popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'START_CRAWL') {
        startCrawl(message.startUrl, message.type, message.initialLinks).then(() => {
            sendResponse({ status: 'started' });
        });
        return true;
    } else if (message.action === 'GET_STATUS') {
        getCrawlState().then(state => {
            sendResponse({
                isCrawling: state.isCrawling,
                count: state.visited.length,
                queueLength: state.queue.length
            });
        });
        return true;
    } else if (message.action === 'STOP_CRAWL') {
        stopCrawl().then(() => {
            sendResponse({ status: 'stopped' });
        });
        return true;
    } else if (message.action === 'GET_RESULTS') {
        getCrawlState().then(state => {
            sendResponse({ results: state.results });
        });
        return true;
    }
});

async function startCrawl(startUrl, type, initialLinks = []) {
    const domain = new URL(startUrl).hostname;

    const state = {
        isCrawling: true,
        visited: [],
        queue: [startUrl],
        results: [],
        domain: domain,
        maxPages: 100,
        crawlerTabId: null
    };

    // Add initial links
    if (initialLinks && initialLinks.length > 0) {
        initialLinks.forEach(link => {
            try {
                const linkUrl = new URL(link);
                if (linkUrl.hostname === domain) {
                    linkUrl.hash = '';
                    const cleanLink = linkUrl.href;
                    if (cleanLink !== startUrl && !state.queue.includes(cleanLink)) {
                        state.queue.push(cleanLink);
                    }
                }
            } catch (e) { }
        });
    }

    // Create a new tab for crawling
    const tab = await chrome.tabs.create({ url: startUrl, active: false });
    state.crawlerTabId = tab.id;
    await saveCrawlState(state);
}

// Stop Crawl
async function stopCrawl() {
    const state = await getCrawlState();
    state.isCrawling = false;
    if (state.crawlerTabId) {
        chrome.tabs.remove(state.crawlerTabId).catch(() => { });
        state.crawlerTabId = null;
    }
    await saveCrawlState(state);
}

// Listen for tab updates
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete') {
        const state = await getCrawlState();
        if (state.isCrawling && tabId === state.crawlerTabId) {
            // Check if this URL is valid for our crawl usage
            // Sometimes onUpdated fires multiple times or for iframes
            // We rely on the logic in scrapePage to determine if we should process
            setTimeout(() => scrapePage(tabId, tab.url), 1000);
        }
    }
});

// Handle tab closure
chrome.tabs.onRemoved.addListener(async (tabId) => {
    const state = await getCrawlState();
    if (state.isCrawling && tabId === state.crawlerTabId) {
        state.isCrawling = false;
        state.crawlerTabId = null;
        await saveCrawlState(state);
        finishCrawl(state);
    }
});


async function scrapePage(tabId, url) {
    let state = await getCrawlState();

    // Re-verify scraping condition to avoid race conditions
    if (!state.isCrawling || state.crawlerTabId !== tabId) return;

    const normalize = (u) => {
        try {
            const urlObj = new URL(u);
            urlObj.hash = '';
            return urlObj.href;
        } catch (e) { return null; }
    };

    const normalizedUrl = normalize(url);

    // Logic: if already visited, skip scraping but continue queue
    if (!normalizedUrl || (state.visited.includes(normalizedUrl) && state.results.find(r => r.url === normalizedUrl))) {
        processNext(state);
        return;
    }

    state.visited.push(normalizedUrl);
    await saveCrawlState(state); // Save progress

    console.log('Scraping:', normalizedUrl);

    try {
        const scriptingResult = await chrome.scripting.executeScript({
            target: { tabId: tabId },
            func: () => {
                return {
                    title: document.title,
                    links: Array.from(document.links).map(a => a.href)
                };
            }
        });

        const data = scriptingResult[0].result;

        // Refresh state before modify (in case of async changes, though unlikely single thread)
        // state = await getCrawlState(); 
        state.results.push({ url: normalizedUrl, title: data.title });

        const links = data.links;
        links.forEach(nextUrl => {
            try {
                const nextUrlObj = new URL(nextUrl);
                const normalizedNext = normalize(nextUrlObj.href);

                if (nextUrlObj.protocol.startsWith('http') && nextUrlObj.hostname === state.domain && normalizedNext) {
                    const extensionsToIgnore = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.pdf', '.zip', '.ico', '.woff', '.woff2'];
                    const isAsset = extensionsToIgnore.some(ext => nextUrlObj.pathname.toLowerCase().endsWith(ext));

                    if (!isAsset && !state.visited.includes(normalizedNext) && !state.queue.includes(normalizedNext)) {
                        state.queue.push(normalizedNext);
                    }
                }
            } catch (e) { }
        });

        await saveCrawlState(state);

        chrome.runtime.sendMessage({
            action: 'CRAWL_PROGRESS',
            count: state.visited.length,
            queue: state.queue.length
        }).catch(() => { });

    } catch (e) {
        console.error('Script injection failed', e);
    }

    // Reload state to check limits
    state = await getCrawlState();
    if (state.visited.length >= state.maxPages) {
        await stopCrawl();
        finishCrawl(state);
        return;
    }

    processNext(state);
}

async function processNext(state) {
    if (!state.isCrawling) return;

    if (state.queue.length === 0) {
        await stopCrawl();
        finishCrawl(state);
        return;
    }

    const nextUrl = state.queue.shift();
    await saveCrawlState(state);

    chrome.tabs.update(state.crawlerTabId, { url: nextUrl }).catch(async (e) => {
        await stopCrawl();
        finishCrawl(state);
    });
}

function finishCrawl(state) {
    console.log('Crawl finished. Processing results...');

    // Sort results alphabetically by URL
    state.results.sort((a, b) => a.url.localeCompare(b.url));

    const structure = generateStructure(state.results);

    // Auto Download CSV from Background
    try {
        console.log('Generating CSV...');
        const csvContent = generateCSV(state.results);

        // Create a data URL
        const dataUrl = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csvContent);

        console.log('Triggering download...');
        chrome.downloads.download({
            url: dataUrl,
            filename: 'sitemap.csv',
            saveAs: false // Download immediately
        }).then((id) => {
            console.log('Download started with ID:', id);
        }).catch(e => {
            console.error('Download failed:', e);
        });

    } catch (e) {
        console.error('CSV Generation/Download failed:', e);
    }

    chrome.runtime.sendMessage({
        action: 'CRAWL_COMPLETE',
        results: state.results,
        structure: structure
    }).catch(() => { });
}

function generateCSV(results) {
    const header = ['URL', 'Title'];
    const rows = results.map(r => [r.url, r.title]);
    return [header, ...rows].map(e => e.map(i => `"${(i || '').replace(/"/g, '""')}"`).join(',')).join('\n');
}

function generateStructure(results) {
    const categories = {};
    results.forEach(item => {
        try {
            const urlObj = new URL(item.url);
            const path = urlObj.pathname;
            const parts = path.split('/').filter(p => p);

            let currentPath = '/';
            if (parts.length > 0) {
                if (path.endsWith('/') || !path.includes('.')) {
                    currentPath = path;
                } else {
                    const lastSlashIndex = path.lastIndexOf('/');
                    currentPath = path.substring(0, lastSlashIndex + 1);
                }
            }

            if (!categories[currentPath]) {
                categories[currentPath] = { count: 0, examples: [] };
            }
            categories[currentPath].count++;
            if (categories[currentPath].examples.length < 3) {
                categories[currentPath].examples.push(item.url);
            }
        } catch (e) { }
    });

    return categories;
}
