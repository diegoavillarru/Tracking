const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const { autoUpdater } = require('electron-updater');

let mainWindow;
let pythonProcess = null;

app.whenReady().then(() => {
    mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    });

    mainWindow.loadFile('index.html');

    // Buscar actualizaciones automáticamente al iniciar la app
    autoUpdater.checkForUpdatesAndNotify();
});

// Eventos del actualizador automático
autoUpdater.on('update-available', () => {
    console.log('¡Hay una nueva actualización disponible!');
});

autoUpdater.on('update-downloaded', () => {
    autoUpdater.quitAndInstall();
});

// Iniciar Tracking Normal
ipcMain.on('start-tracking', () => {
    if (!pythonProcess) {
        const scriptPath = path.join(__dirname, 'python_script', 'tracker.py');
        pythonProcess = spawn('python', [scriptPath]);

        pythonProcess.stdout.on('data', (data) => {
            console.log(`stdout: ${data}`);
        });

        pythonProcess.stderr.on('data', (data) => {
            console.error(`stderr: ${data}`);
        });

        pythonProcess.on('close', (code) => {
            console.log(`Proceso Python cerrado con código ${code}`);
            pythonProcess = null;
        });
    }
});

// Calibrar Pantalla por Esquinas
ipcMain.on('calibrate-screen', () => {
    if (!pythonProcess) {
        const scriptPath = path.join(__dirname, 'python_script', 'tracker.py');
        const calibrationProcess = spawn('python', [scriptPath, '--calibrate']);

        calibrationProcess.stdout.on('data', (data) => {
            console.log(`Calibración stdout: ${data}`);
        });

        calibrationProcess.stderr.on('data', (data) => {
            console.error(`Calibración stderr: ${data}`);
        });

        calibrationProcess.on('close', (code) => {
            console.log(`Calibración finalizada con código ${code}`);
        });
    }
});

// Detener Tracking
ipcMain.on('stop-tracking', () => {
    if (pythonProcess) {
        pythonProcess.kill();
        pythonProcess = null;
    }
});