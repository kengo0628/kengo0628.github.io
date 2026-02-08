document.addEventListener('DOMContentLoaded', () => {
    const btnScanStructure = document.getElementById('btn-scan-structure');
    const btnScanList = document.getElementById('btn-scan-list');
    const statusArea = document.getElementById('status-area');
    const resultArea = document.getElementById('result-area');
    const statusText = document.getElementById('status-text');
    const urlCount = document.getElementById('url-count');

    btnScanList.addEventListener('click', async () => {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tab) return;

        startCrawl(tab.url, 'list');
    });

    btnScanStructure.addEventListener('click', async () => {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tab) return;

        startCrawl(tab.url, 'structure');
    });

    function startCrawl(url, type) {
        statusArea.classList.remove('hidden');
        resultArea.classList.add('hidden');
        statusText.textContent = 'Initializing...';

        // Get links from the current page DOM to handle JS-rendered content better
        chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
            const tabId = tabs[0].id;

            try {
                const results = await chrome.scripting.executeScript({
                    target: { tabId: tabId },
                    func: () => {
                        return Array.from(document.links).map(a => a.href);
                    }
                });

                const initialLinks = results[0].result || [];

                statusText.textContent = `Found ${initialLinks.length} initial links. Starting crawl...`;

                chrome.runtime.sendMessage({
                    action: 'START_CRAWL',
                    startUrl: url,
                    type: type,
                    initialLinks: initialLinks
                });

            } catch (e) {
                console.error('Script execution failed:', e);
                // Fallback to URL only
                chrome.runtime.sendMessage({
                    action: 'START_CRAWL',
                    startUrl: url,
                    type: type,
                    initialLinks: []
                });
            }
        });
    }

    chrome.runtime.onMessage.addListener((message) => {
        if (message.action === 'CRAWL_PROGRESS') {
            urlCount.textContent = message.count;
            statusText.textContent = `Crawling... (Queue: ${message.queue})`;
        } else if (message.action === 'CRAWL_COMPLETE') {
            statusText.textContent = 'Completed!';
            urlCount.textContent = message.results.length;
            resultArea.classList.remove('hidden');

            // Store results globally for export
            window.lastResults = message.results;
            window.lastStructure = message.structure;

            renderPreview(message.results, message.structure);
        }
    });

    document.getElementById('btn-export-csv').addEventListener('click', () => {
        if (!window.lastResults) return;
        const csvContent = generateCSV(window.lastResults);
        downloadCSV(csvContent, 'sitemap.csv');
    });

    document.getElementById('btn-export-sheets').addEventListener('click', async () => {
        if (!window.lastResults) return;

        const btn = document.getElementById('btn-export-sheets');
        const originalText = btn.textContent;
        btn.textContent = 'Processing...';
        btn.disabled = true;

        try {
            // 1. Get Token
            const token = await GoogleSheets.getToken();

            // 2. Create Sheet
            const dateStr = new Date().toISOString().slice(0, 10);
            const sheetData = await GoogleSheets.createSpreadsheet(`Sitemap Export - ${dateStr}`, token);
            const spreadsheetId = sheetData.spreadsheetId;
            const spreadsheetUrl = sheetData.spreadsheetUrl;

            // 3. Prepare Data
            // Use Structure or List? Let's do List for now as it makes more sense for a spreadsheet
            // Or maybe two sheets? For simplicity, just the list.
            const headers = ['URL', 'Title', 'Category (Guessed)'];
            const data = window.lastResults.map(r => {
                // Guess category
                let cat = '/';
                try {
                    const p = new URL(r.url).pathname;
                    cat = p.split('/').slice(0, 2).join('/') || '/';
                } catch (e) { }
                return [r.url, r.title, cat];
            });

            // 4. Write Data
            await GoogleSheets.appendValues(spreadsheetId, 'Sheet1!A1', [headers, ...data], token);

            alert(`Export Successful!\nOpened in new tab.`);
            chrome.tabs.create({ url: spreadsheetUrl });

        } catch (err) {
            console.error(err);
            alert('Export failed. See console for details.\nEnsure you have set up the Client ID in manifest.json.');
        } finally {
            btn.textContent = originalText;
            btn.disabled = false;
        }
    });
});

function renderPreview(results, structure) {
    const preview = document.getElementById('preview');
    preview.innerHTML = '';

    if (structure) {
        const table = document.createElement('table');
        table.style.width = '100%';
        table.style.borderCollapse = 'collapse';
        table.innerHTML = `<tr><th style="text-align:left">Category</th><th>Count</th></tr>`;

        // Sort categories alphabetically
        const sortedEntries = Object.entries(structure).sort((a, b) => a[0].localeCompare(b[0]));

        for (const [cat, data] of sortedEntries) {
            const row = table.insertRow();
            row.innerHTML = `<td style="border-bottom:1px solid #eee">${cat}</td><td style="border-bottom:1px solid #eee">${data.count}</td>`;
        }
        preview.appendChild(table);
    } else {
        // List view
        const ul = document.createElement('ul');
        results.slice(0, 20).forEach(item => {
            const li = document.createElement('li');
            li.textContent = item.url;
            ul.appendChild(li);
        });
        if (results.length > 20) {
            const li = document.createElement('li');
            li.textContent = `...and ${results.length - 20} more`;
            ul.appendChild(li);
        }
        preview.appendChild(ul);
    }
}

function generateCSV(results) {
    const header = ['URL', 'Title'];
    const rows = results.map(r => [r.url, r.title]);
    return [header, ...rows].map(e => e.map(i => `"${(i || '').replace(/"/g, '""')}"`).join(',')).join('\n');
}

function downloadCSV(content, filename) {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
