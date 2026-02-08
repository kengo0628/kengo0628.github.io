const GoogleSheets = {
    /**
     * Get Auth Token
     */
    getToken: function () {
        return new Promise((resolve, reject) => {
            chrome.identity.getAuthToken({ interactive: true }, function (token) {
                if (chrome.runtime.lastError) {
                    reject(chrome.runtime.lastError);
                } else {
                    resolve(token);
                }
            });
        });
    },

    /**
     * Create a new Spreadsheet
     * @param {string} title 
     * @param {string} token 
     */
    createSpreadsheet: async function (title, token) {
        const response = await fetch('https://sheets.googleapis.com/v4/spreadsheets', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                properties: {
                    title: title
                }
            })
        });
        if (!response.ok) throw new Error('Failed to create spreadsheet');
        return await response.json();
    },

    /**
     * Write data to spreadsheet
     * @param {string} spreadsheetId 
     * @param {string} range e.g. "Sheet1!A1"
     * @param {Array<Array<string>>} values 
     * @param {string} token 
     */
    appendValues: async function (spreadsheetId, range, values, token) {
        const response = await fetch(`https://sheets.googleapis.com/v4/spreadsheets/${spreadsheetId}/values/${range}:append?valueInputOption=USER_ENTERED`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                values: values
            })
        });
        if (!response.ok) throw new Error('Failed to append values');
        return await response.json();
    }
};
