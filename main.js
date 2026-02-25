const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow() {
    const win = new BrowserWindow({
        width: 350,
        height: 350,
        transparent: true,    // Makes the background invisible
        frame: false,          // Removes the window title bar/borders
        alwaysOnTop: true,    // Keeps Zora floating over other apps
        resizable: false,      // Keeps the orb at a consistent size
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    });

    // Points to the new folder structure we created
    win.loadFile('www/index.html');
}

// Launch the window when Electron is ready
app.whenReady().then(createWindow);

// Quit the app when all windows are closed (Windows & Linux standard)
app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});