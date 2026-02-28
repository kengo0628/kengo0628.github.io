document.addEventListener('DOMContentLoaded', () => {
    const csvUrl = 'frienda_database_complete.csv';
    let allData = [];

    // DOM Elements
    const cardsContainer = document.getElementById('cards-container');
    const searchInput = document.getElementById('search-input');
    const typeFilter = document.getElementById('type-filter');
    const rarityFilter = document.getElementById('rarity-filter');
    const seriesFilter = document.getElementById('series-filter');
    const sortSelect = document.getElementById('sort-select');
    const moveTypeFilter = document.getElementById('move-type-filter');
    const totalCount = document.getElementById('total-count');

    // Modal Elements
    const modal = document.getElementById('image-modal');
    const modalImg = document.getElementById('modal-image');
    const captionText = document.getElementById('caption');
    const span = document.getElementsByClassName("close")[0];

    // Feedback Modal Elements
    const feedbackModal = document.getElementById('feedback-modal');
    // GAS Web App URL
    const GAS_URL = 'https://script.google.com/macros/s/AKfycbymHMAl3L-qMcFDI5xOdUY49deV3syDb8Bj8qMjuYypKamhVUdMKLmuum2DnMZ1IBnY/exec';

    // Close Modal Events
    if (span) {
        span.onclick = function () {
            modal.style.display = "none";
        }
    }

    // Close when clicking outside request
    window.onclick = function (event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
        if (event.target == feedbackModal) {
            feedbackModal.style.display = "none";
        }
    }

    // Type mapping to English for CSS classes
    const typeMap = {
        'ノーマル': 'normal', 'ほのお': 'fire', 'みず': 'water', 'でんき': 'electric',
        'くさ': 'grass', 'こおり': 'ice', 'かくとう': 'fighting', 'ドク': 'poison', 'どく': 'poison',
        'じめん': 'ground', 'ひこう': 'flying', 'エスパー': 'psychic', 'ムシ': 'bug', 'むし': 'bug',
        'いわ': 'rock', 'ゴースト': 'ghost', 'ドラゴン': 'dragon', 'あく': 'dark',
        'はがね': 'steel', 'フェアリー': 'fairy',
        'ステラ': 'stellar',
        '草': 'grass', '水': 'water', '格闘': 'fighting', '悪': 'dark' // Handle variations
    };

    // Initialize
    fetchData();

    // Event Listeners
    searchInput.addEventListener('input', filterAndRender);
    typeFilter.addEventListener('change', filterAndRender);
    moveTypeFilter.addEventListener('change', filterAndRender);
    rarityFilter.addEventListener('change', filterAndRender);
    seriesFilter.addEventListener('change', filterAndRender);
    sortSelect.addEventListener('change', filterAndRender);

    async function fetchData() {
        try {
            const response = await fetch(csvUrl);
            const csvText = await response.text();
            allData = parseCSV(csvText);

            // In case of duplicate headers or empty lines, clean up
            allData = allData.filter(item => item.ID && item.Name);

            // Populate Filters
            populateTypeFilter();
            populateMoveTypeFilter();
            populateSeriesFilter();

            filterAndRender();
        } catch (error) {
            console.error('Error loading CSV:', error);
            cardsContainer.innerHTML = '<div class="loading">データの読み込みにしっぱいしました。</div>';
        }
    }

    function populateTypeFilter() {
        const types = new Set();
        allData.forEach(item => {
            if (item.Type) {
                // Split multiple types
                const currentTypes = item.Type.replace(/"/g, '').split(/[,\s、]+/);
                currentTypes.forEach(t => {
                    const tClean = t.trim();
                    if (tClean) types.add(tClean);
                });
            }
        });

        const sortedTypes = Array.from(types).sort();

        // Clear existing (except first)
        typeFilter.innerHTML = '<option value="">全てのタイプ</option>';

        sortedTypes.forEach(t => {
            const option = document.createElement('option');
            option.value = t;
            option.textContent = t;
            typeFilter.appendChild(option);
        });
    }

    function populateMoveTypeFilter() {
        const moveTypes = new Set();
        allData.forEach(item => {
            if (item.MoveType) {
                // Split multiple types if any (though usually one, handle similarly for safety)
                const currentTypes = item.MoveType.replace(/"/g, '').split(/[,\s、]+/);
                currentTypes.forEach(t => {
                    const tClean = t.trim();
                    if (tClean) moveTypes.add(tClean);
                });
            }
        });

        const sortedMoveTypes = Array.from(moveTypes).sort();

        moveTypeFilter.innerHTML = '<option value="">全てのわざタイプ</option>';

        sortedMoveTypes.forEach(t => {
            const option = document.createElement('option');
            option.value = t;
            option.textContent = t;
            moveTypeFilter.appendChild(option);
        });
    }

    function populateSeriesFilter() {
        const series = new Set();
        allData.forEach(item => {
            if (item.Series) series.add(item.Series);
        });

        // Convert to array and sort
        // Sort order: 1だん, 2だん, ..., 5だん, ベストタッグ1だん, ..., スペシャル, その他
        const seriesArray = Array.from(series);

        seriesArray.sort((a, b) => {
            const getRank = (s) => {
                if (s === '1だん') return 10;
                if (s === '2だん') return 20;
                if (s === '3だん') return 30;
                if (s === '4だん') return 40;
                if (s === '5だん') return 50;
                if (s === 'ベストタッグ1だん') return 110;
                if (s === 'ベストタッグ2だん') return 120;
                if (s === 'ベストタッグ3だん') return 130;
                if (s === 'ベストタッグ4だん') return 140;
                if (s === 'スペシャル') return 900;
                return 1000;
            };
            return getRank(a) - getRank(b);
        });

        seriesArray.forEach(s => {
            const option = document.createElement('option');
            option.value = s;
            option.textContent = s;
            seriesFilter.appendChild(option);
        });
    }

    function parseCSV(text) {
        const lines = text.trim().split('\n');
        const headers = lines[0].split(',').map(h => h.trim());
        const result = [];

        // Advanced CSV splitting to handle quoted fields like "ドラゴン, じめん"
        for (let i = 1; i < lines.length; i++) {
            const line = lines[i];
            const row = {};
            let currentField = '';
            let inQuotes = false;
            let fieldIndex = 0;

            for (let charIndex = 0; charIndex < line.length; charIndex++) {
                const char = line[charIndex];

                if (char === '"') {
                    inQuotes = !inQuotes;
                } else if (char === ',' && !inQuotes) {
                    // End of field
                    if (fieldIndex < headers.length) {
                        row[headers[fieldIndex]] = currentField.trim();
                    }
                    currentField = '';
                    fieldIndex++;
                } else {
                    currentField += char;
                }
            }
            // Last field
            if (fieldIndex < headers.length) {
                row[headers[fieldIndex]] = currentField.trim();
            }

            result.push(row);
        }
        return result;
    }

    function filterAndRender() {
        const searchText = searchInput.value.toLowerCase();
        const typeValue = typeFilter.value; // Get Type Filter Value
        const moveTypeValue = moveTypeFilter.value; // Get Move Type Filter Value
        const rarityValue = rarityFilter.value;
        const seriesValue = seriesFilter.value;
        const sortValue = sortSelect.value;

        let filtered = allData.filter(item => {
            // Search Text
            const matchName = item.Name && item.Name.toLowerCase().includes(searchText);
            const matchId = item.ID && item.ID.toLowerCase().includes(searchText);
            // Search text check for type is okay to leave or remove if redundant
            const matchTypeSearch = item.Type && item.Type.toLowerCase().includes(searchText);
            if (searchText && !matchName && !matchId && !matchTypeSearch) return false;

            // Type Filter
            if (typeValue) {
                const itemTypes = item.Type ? item.Type.replace(/"/g, '').split(/[,\s、]+/).map(t => t.trim()) : [];
                if (!itemTypes.includes(typeValue)) return false;
            }

            // Move Type Filter
            if (moveTypeValue) {
                const itemMoveTypes = item.MoveType ? item.MoveType.replace(/"/g, '').split(/[,\s、]+/).map(t => t.trim()) : [];
                if (!itemMoveTypes.includes(moveTypeValue)) return false;
            }

            // Series Filter
            if (seriesValue) {
                if (item.Series !== seriesValue) return false;
            }

            // Rarity Filter
            if (rarityValue) {
                if (rarityValue === 'スペシャル') {
                    if (item.Rarity !== 'スペシャル') return false;
                } else {
                    // Check if numeric rarity matches
                    // Item rarity might be "4" or "4 (Star)" etc. just checking startsWith or equality
                    if (!item.Rarity || !item.Rarity.toString().startsWith(rarityValue)) return false;
                }
            }
            return true;
        });

        // Sort
        filtered.sort((a, b) => {
            if (sortValue === 'id') {
                return a.ID.localeCompare(b.ID);
            }
            if (sortValue === 'pokeene_desc') {
                return (parseInt(b.PokeEne) || 0) - (parseInt(a.PokeEne) || 0);
            }
            if (sortValue === 'pokeene_asc') {
                const valA = parseInt(a.PokeEne) || 0;
                const valB = parseInt(b.PokeEne) || 0;
                if (valA === 0 && valB === 0) return 0;
                if (valA === 0) return 1;
                if (valB === 0) return -1;
                return valA - valB;
            }
            if (sortValue === 'atk_desc') {
                return (parseInt(b.ATK) || 0) - (parseInt(a.ATK) || 0);
            }
            if (sortValue === 'atk_asc') {
                const valA = parseInt(a.ATK) || 0;
                const valB = parseInt(b.ATK) || 0;
                if (valA === 0 && valB === 0) return 0;
                if (valA === 0) return 1;
                if (valB === 0) return -1;
                return valA - valB;
            }
            if (sortValue === 'def_desc') {
                return (parseInt(b.DEF) || 0) - (parseInt(a.DEF) || 0);
            }
            if (sortValue === 'def_asc') {
                const valA = parseInt(a.DEF) || 0;
                const valB = parseInt(b.DEF) || 0;
                if (valA === 0 && valB === 0) return 0;
                if (valA === 0) return 1;
                if (valB === 0) return -1;
                return valA - valB;
            }
            if (sortValue === 'sp_atk_desc') {
                return (parseInt(b['SP.ATK']) || 0) - (parseInt(a['SP.ATK']) || 0);
            }
            if (sortValue === 'sp_atk_asc') {
                const valA = parseInt(a['SP.ATK']) || 0;
                const valB = parseInt(b['SP.ATK']) || 0;
                if (valA === 0 && valB === 0) return 0;
                if (valA === 0) return 1;
                if (valB === 0) return -1;
                return valA - valB;
            }
            if (sortValue === 'sp_def_desc') {
                return (parseInt(b['SP.DEF']) || 0) - (parseInt(a['SP.DEF']) || 0);
            }
            if (sortValue === 'sp_def_asc') {
                const valA = parseInt(a['SP.DEF']) || 0;
                const valB = parseInt(b['SP.DEF']) || 0;
                if (valA === 0 && valB === 0) return 0;
                if (valA === 0) return 1;
                if (valB === 0) return -1;
                return valA - valB;
            }
            if (sortValue === 'speed_desc') {
                return (parseInt(b.Speed) || 0) - (parseInt(a.Speed) || 0);
            }
            if (sortValue === 'speed_asc') {
                const valA = parseInt(a.Speed) || 0;
                const valB = parseInt(b.Speed) || 0;
                if (valA === 0 && valB === 0) return 0;
                if (valA === 0) return 1;
                if (valB === 0) return -1;
                return valA - valB;
            }
            if (sortValue === 'hp_desc') {
                return (parseInt(b.HP) || 0) - (parseInt(a.HP) || 0);
            }
            if (sortValue === 'hp_asc') {
                const valA = parseInt(a.HP) || 0;
                const valB = parseInt(b.HP) || 0;
                if (valA === 0 && valB === 0) return 0;
                if (valA === 0) return 1;
                if (valB === 0) return -1;
                return valA - valB;
            }
            return 0;
        });

        totalCount.textContent = filtered.length;
        renderCards(filtered);
    }

    function renderCards(data) {
        cardsContainer.innerHTML = '';
        if (data.length === 0) {
            cardsContainer.innerHTML = '<div class="loading">ポケモンが見つかりませんでした。</div>';
            return;
        }

        data.forEach(item => {
            const card = document.createElement('div');
            card.className = 'card';

            const imageUrl = item.OriginalURL ? item.OriginalURL : (item.ImageFile ? `frienda_images/${item.ImageFile}` : '');

            // Format Rarity
            let rarityDisplay = '';
            if (item.Rarity === 'スペシャル') {
                rarityDisplay = 'SP';
            } else if (item.Rarity) {
                const stars = parseInt(item.Rarity);
                if (!isNaN(stars)) {
                    rarityDisplay = '★'.repeat(stars);
                } else {
                    rarityDisplay = item.Rarity;
                }
            }

            // Variant Badge
            let variantHtml = '';
            if (item.Variant) {
                let variantClass = '';
                if (item.Variant === 'パラレル') variantClass = 'variant-parallel';
                if (item.Variant === 'ワンダー') variantClass = 'variant-wonder';
                if (item.Variant === '色違い') variantClass = 'variant-shiny';
                variantHtml = `<span class="variant-badge ${variantClass}">${item.Variant}</span>`;
            }

            // Format Types
            let typesHtml = '';
            if (item.Type) {
                // Remove quotes handles in parse, but split multiple types
                const types = item.Type.replace(/"/g, '').split(/[,\s、]+/);
                types.forEach(t => {
                    const tClean = t.trim();
                    if (tClean) {
                        const engType = typeMap[tClean] || 'normal';
                        typesHtml += `<span class="type-badge type-${engType}">${tClean}</span>`;
                    }
                });
            }

            // Move details
            const moveHtml = item.Move ? `
                <div class="stat-item">
                    <span class="stat-label">わざ</span>
                    <span class="stat-value">${item.Move}</span>
                </div>
            ` : '';

            const specialHtml = item.Special ? `
                <div class="stat-item main-stat">
                    <span class="stat-label">とくべつ</span>
                    <span class="stat-value">${item.Special}</span>
                </div>
            ` : '';

            card.innerHTML = `
                <div class="card-image" style="cursor: pointer;" onclick="openModal('${imageUrl}', '${item.Name}')">
                     <img src="${imageUrl}" alt="${item.Name}" loading="lazy" onerror="this.style.display='none'">
                </div>
                <div class="card-content">
                    <div class="card-header">
                        <span class="card-id">${item.ID}</span>
                        <div style="display:flex; gap:4px; align-items:center;">
                            ${variantHtml}
                            <span class="card-rarity">${rarityDisplay}</span>
                        </div>
                    </div>
                    <h2 class="card-name">${item.Name}</h2>
                    <div class="types-container">${typesHtml}</div>
                    
                    <div class="stats-grid">
                        <div class="stat-item main-stat" style="grid-column: 1 / -1; justify-content: center;">
                            <span class="stat-label">ポケエネ：</span>
                            <span class="stat-value" style="font-size: 1.2rem; margin-left:8px;">${item.PokeEne || '-'}</span>
                        </div>
                        <div class="stat-item"><span class="stat-label">HP</span> <span class="stat-value">${item.HP || '-'}</span></div>
                        <div class="stat-item"><span class="stat-label">こうげき</span> <span class="stat-value">${item.ATK || '-'}</span></div>
                        <div class="stat-item"><span class="stat-label">ぼうぎょ</span> <span class="stat-value">${item.DEF || '-'}</span></div>
                        <div class="stat-item"><span class="stat-label">すばやさ</span> <span class="stat-value">${item.Speed || '-'}</span></div>
                        <div class="stat-item"><span class="stat-label">とくこう</span> <span class="stat-value">${item['SP.ATK'] || '-'}</span></div>
                        <div class="stat-item"><span class="stat-label">とくぼう</span> <span class="stat-value">${item['SP.DEF'] || '-'}</span></div>
                        <div style="grid-column: 1 / -1;">
                            ${moveHtml}
                            ${specialHtml}
                        </div>
                    </div>
                    <button class="feedback-btn" onclick="showFeedbackModal('${item.ID}', '${item.Name}')">間違いを報告</button>
                </div>
            `;
            cardsContainer.appendChild(card);
        });
    }

    // Expose openModal to global scope for inline onclick
    window.openModal = function (src, name) {
        if (!src) return;
        modal.style.display = "block";
        modalImg.src = src;
        captionText.innerHTML = name;
    }

    // Populate Feedback Options
    function populateFeedbackOptions() {
        // Types
        const typeContainer = document.getElementById('feedback-value-type-container');
        typeContainer.innerHTML = '';
        const types = new Set();
        // Move Types
        const moveTypeSelect = document.getElementById('feedback-value-movetype');
        moveTypeSelect.innerHTML = '<option value="">選択してください</option>';
        const moveTypes = new Set();

        allData.forEach(item => {
            if (item.Type) {
                const currentTypes = item.Type.replace(/"/g, '').split(/[,\s、]+/);
                currentTypes.forEach(t => { if (t.trim()) types.add(t.trim()); });
            }
            if (item.MoveType) {
                const currentMoveTypes = item.MoveType.replace(/"/g, '').split(/[,\s、]+/);
                currentMoveTypes.forEach(t => { if (t.trim()) moveTypes.add(t.trim()); });
            }
        });

        // Sort and populate Types
        Array.from(types).sort().forEach(t => {
            const label = document.createElement('label');
            label.style.display = 'inline-flex';
            label.style.alignItems = 'center';
            label.style.marginRight = '10px';
            label.style.cursor = 'pointer';

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = t;
            checkbox.name = 'feedback-type';
            checkbox.style.width = 'auto';
            checkbox.style.marginRight = '4px';

            // Limit to 2
            checkbox.addEventListener('change', function () {
                const checked = document.querySelectorAll('input[name="feedback-type"]:checked');
                if (checked.length > 2) {
                    this.checked = false;
                    alert('タイプは2つまでしか選べません');
                }
            });

            label.appendChild(checkbox);
            label.appendChild(document.createTextNode(t));
            typeContainer.appendChild(label);
        });

        // Sort and populate Move Types
        Array.from(moveTypes).sort().forEach(t => {
            const option = document.createElement('option');
            option.value = t;
            option.textContent = t;
            moveTypeSelect.appendChild(option);
        });
    }

    // Toggle Input Fields based on selection
    document.getElementById('feedback-field').addEventListener('change', function () {
        const field = this.value;
        document.getElementById('input-container-text').style.display = 'none';
        document.getElementById('input-container-rarity').style.display = 'none';
        document.getElementById('input-container-type').style.display = 'none';
        document.getElementById('input-container-movetype').style.display = 'none';

        if (field === 'Rarity') {
            document.getElementById('input-container-rarity').style.display = 'block';
        } else if (field === 'Type') {
            document.getElementById('input-container-type').style.display = 'block';
        } else if (field === 'MoveType') {
            document.getElementById('input-container-movetype').style.display = 'block';
        } else {
            document.getElementById('input-container-text').style.display = 'block';
        }
    });

    window.showFeedbackModal = function (id, name) {
        document.getElementById('feedback-id').value = id;
        document.getElementById('feedback-name').value = name;

        // Reset
        document.getElementById('feedback-field').value = 'HP';
        document.getElementById('feedback-field').dispatchEvent(new Event('change')); // Trigger toggle

        document.getElementById('feedback-value').value = '';
        document.getElementById('feedback-value-rarity').value = '5';
        document.getElementById('feedback-value-movetype').value = '';
        document.querySelectorAll('input[name="feedback-type"]').forEach(cb => cb.checked = false);

        populateFeedbackOptions(); // Ensure options are loaded (idempotent-ish, or check if empty)

        const feedbackModal = document.getElementById('feedback-modal');
        feedbackModal.style.display = "block";
    }

    window.closeFeedbackModal = function () {
        const feedbackModal = document.getElementById('feedback-modal');
        feedbackModal.style.display = "none";
    }

    window.submitFeedback = function () {
        const id = document.getElementById('feedback-id').value;
        const name = document.getElementById('feedback-name').value;
        const field = document.getElementById('feedback-field').value;

        let value = '';

        if (field === 'Rarity') {
            value = document.getElementById('feedback-value-rarity').value;
        } else if (field === 'Type') {
            const checked = document.querySelectorAll('input[name="feedback-type"]:checked');
            value = Array.from(checked).map(cb => cb.value).join(', ');
        } else if (field === 'MoveType') {
            value = document.getElementById('feedback-value-movetype').value;
        } else {
            value = document.getElementById('feedback-value').value;
        }

        if (!value) {
            alert('正しい値を入力してください');
            return;
        }

        const btn = document.getElementById('submit-feedback-btn');
        btn.disabled = true;
        btn.textContent = '送信中...';

        // Construct URL for GET request (simpler for GAS Web App without CORS issues usually)
        // Or POST with no-cors mode
        const url = `${GAS_URL}?ID=${encodeURIComponent(id)}&Name=${encodeURIComponent(name)}&Field=${encodeURIComponent(field)}&Value=${encodeURIComponent(value)}`;

        fetch(url, {
            method: 'POST',
            mode: 'no-cors', // Important for GAS
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `ID=${encodeURIComponent(id)}&Name=${encodeURIComponent(name)}&Field=${encodeURIComponent(field)}&Value=${encodeURIComponent(value)}`
        })
            .then(() => {
                alert('報告ありがとうございました！');
                closeFeedbackModal();
            })
            .catch(err => {
                console.error('Error:', err);
                alert('送信に失敗しました。');
            })
            .finally(() => {
                btn.disabled = false;
                btn.textContent = '送信';
            });
    }
});
