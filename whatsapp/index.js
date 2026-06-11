const { makeWASocket, useMultiFileAuthState, fetchLatestBaileysVersion, makeCacheableSignalKeyStore, Browsers } = require('@whiskeysockets/baileys');
const fs = require('fs');
const path = require('path');

const SESSION_PATH = './session';
const SESSION_B64 = process.env.WHATSAPP_SESSION;
const TO_NUMBER = process.env.TO_NUMBER;

if (!TO_NUMBER) {
    console.error('❌ Missing TO_NUMBER env var');
    process.exit(1);
}
if (!SESSION_B64) {
    console.error('❌ Missing WHATSAPP_SESSION env var');
    process.exit(1);
}

async function main() {
    // Decode and write session files
    const files = JSON.parse(Buffer.from(SESSION_B64, 'base64').toString());
    console.log('Session entries:', Object.keys(files).length);
    for (const [relPath, content] of Object.entries(files)) {
        const fullPath = path.join(SESSION_PATH, relPath);
        fs.mkdirSync(path.dirname(fullPath), { recursive: true });
        fs.writeFileSync(fullPath, Buffer.from(content, 'base64'));
    }

    // Verify creds.json exists
    const credsPath = path.join(SESSION_PATH, 'creds.json');
    if (!fs.existsSync(credsPath)) {
        console.error('❌ creds.json not found in session!');
        process.exit(1);
    }
    const creds = JSON.parse(fs.readFileSync(credsPath, 'utf-8'));
    console.log('Registered ID:', creds?.me?.id || 'unknown');

    console.log('Session files written, connecting...');

    const { state, saveCreds } = await useMultiFileAuthState(SESSION_PATH);
    const { version } = await fetchLatestBaileysVersion();
    const sock = makeWASocket({
        version,
        browser: Browsers.windows('Chrome'),
        auth: {
            creds: state.creds,
            keys: makeCacheableSignalKeyStore(state.keys),
        },
        syncFullHistory: false,
        markOnlineOnConnect: false,
    });

    sock.ev.on('creds.update', saveCreds);

    // Timeout guard
    const timeout = setTimeout(() => {
        console.error('⏰ Timed out waiting for connection');
        process.exit(1);
    }, 30000);

    sock.ev.on('connection.update', async ({ connection, lastDisconnect }) => {
        console.log('📡 Connection state:', connection);

        if (connection === 'open') {
            clearTimeout(timeout);
            console.log('✅ WhatsApp connected');
            try {
                const briefingPath = path.join(__dirname, '..', 'briefing.txt');
                const briefing = fs.readFileSync(briefingPath, 'utf-8');
                const jid = TO_NUMBER.includes('@s.whatsapp.net')
                    ? TO_NUMBER
                    : TO_NUMBER + '@s.whatsapp.net';
                console.log(`📤 Sending to ${jid}...`);
                await sock.sendMessage(jid, { text: briefing });
                console.log('✅ Briefing sent! Waiting for delivery...');
            await new Promise(r => setTimeout(r, 5000));
            } catch (err) {
                console.error('❌ Send failed:', err);
            }
            process.exit(0);
        }

        if (connection === 'close') {
            clearTimeout(timeout);
            const err = lastDisconnect?.error;
            const reason = err?.output?.statusCode || err?.message || err?.toString() || 'unknown';
            console.error(`❌ Connection closed. Reason: ${reason}`);
            process.exit(1);
        }
    });
}

main();
