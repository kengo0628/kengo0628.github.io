function doPost(e) {
    const lock = LockService.getScriptLock();
    lock.tryLock(10000);

    try {
        const doc = SpreadsheetApp.getActiveSpreadsheet();
        const sheet = doc.getSheetByName('シート1') || doc.getSheets()[0];

        const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
        const newRow = headers.map(header => {
            const headerName = header === 'timestamp' ? 'Date' : header;
            return headerName === 'Date' ? new Date() : e.parameter[headerName];
        });

        sheet.appendRow(newRow);

        return ContentService
            .createTextOutput(JSON.stringify({ 'result': 'success', 'row': newRow }))
            .setMimeType(ContentService.MimeType.JSON);
    } catch (e) {
        return ContentService
            .createTextOutput(JSON.stringify({ 'result': 'error', 'error': e }))
            .setMimeType(ContentService.MimeType.JSON);
    } finally {
        lock.releaseLock();
    }
}

function setup() {
    const doc = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = doc.getSheetByName('シート1') || doc.getSheets()[0];
    sheet.appendRow(['ID', 'Name', 'Field', 'Value', 'Date']);
}
