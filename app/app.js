const express = require('express');
const os = require('os');
const fs = require('fs');
const path = require('path');
const child_process = require('child_process');

const app = express();
const PORT = process.env.PORT || 3000;
const DB_FILE = path.join(__dirname, 'guestbook.json');

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Initialize guestbook JSON database
if (!fs.existsSync(DB_FILE)) {
    fs.writeFileSync(DB_FILE, JSON.stringify([
        { name: "ZipLoot Bot", message: "Welcome to your free lifetime Serv00 Node.js Hosting!", date: new Date().toISOString() }
    ], null, 2));
}

// 1. System Stats Endpoint
app.apiStats = async (req, res) => {
    try {
        const platform = os.platform();
        const uptime = os.uptime();
        const totalMem = os.totalmem();
        const freeMem = os.freemem();
        const cpuModel = os.cpus().length > 0 ? os.cpus()[0].model : "Unknown";
        const cpuCores = os.cpus().length;
        const loadAvg = os.loadavg();
        
        // Execute df -h to get disk space (specifically for the user's home folder)
        let diskInfo = "Unknown";
        try {
            diskInfo = child_process.execSync('df -h ~ | tail -n 1').toString().trim();
        } catch (e) {
            try {
                diskInfo = child_process.execSync('df -h | grep -v tmpfs | head -n 2').toString().trim();
            } catch (diskErr) {
                diskInfo = "N/A";
            }
        }

        res.json({
            platform: platform.toUpperCase(),
            uptime: formatUptime(uptime),
            memory: {
                total: formatBytes(totalMem),
                free: formatBytes(freeMem),
                used: formatBytes(totalMem - freeMem),
                percent: Math.round(((totalMem - freeMem) / totalMem) * 100)
            },
            cpu: {
                model: cpuModel,
                cores: cpuCores,
                load: loadAvg
            },
            disk: diskInfo
        });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};

app.get('/api/stats', app.apiStats);

// 2. Guestbook Endpoints
app.get('/api/guestbook', (req, res) => {
    try {
        const data = JSON.parse(fs.readFileSync(DB_FILE, 'utf-8'));
        res.json(data);
    } catch (err) {
        res.status(500).json({ error: "Failed to read database." });
    }
});

app.post('/api/guestbook', (req, res) => {
    try {
        const { name, message } = req.body;
        if (!name || !message) {
            return res.status(400).json({ error: "Name and message are required." });
        }

        const data = JSON.parse(fs.readFileSync(DB_FILE, 'utf-8'));
        data.unshift({
            name: name.trim().substring(0, 50),
            message: message.trim().substring(0, 500),
            date: new Date().toISOString()
        });

        fs.writeFileSync(DB_FILE, JSON.stringify(data, null, 2));
        res.json({ success: true, message: "Comment added!" });
    } catch (err) {
        res.status(500).json({ error: "Failed to update database." });
    }
});

// Helper Functions
function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatUptime(seconds) {
    const d = Math.floor(seconds / (3600 * 24));
    const h = Math.floor((seconds % (3600 * 24)) / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return `${d}d ${h}h ${m}m ${s}s`;
}

// Serve Frontend index.html for all other routes
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server is running on port ${PORT}`);
});
