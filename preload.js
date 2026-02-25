const fs = require('fs');

window.addEventListener('DOMContentLoaded', () => {
    // Check for updates every 500ms
    setInterval(() => {
        if (fs.existsSync('ui_state.txt')) {
            const status = fs.readFileSync('ui_state.txt', 'utf8');
            document.getElementById('node-version').innerText = status; // Use an ID to show status
        }
    }, 500);
});