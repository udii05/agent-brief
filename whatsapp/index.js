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
    for (const [relPath, content] of Object.entries(files)) {
        const fullPath = path.join(SESSION_PATH, relPath);
        fs.mkdirSync(path.dirname(fullPath), { recursive: true });
        fs.writeFileSync(fullPath, Buffer.from(content, 'base64'));
    }

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
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', async ({ connection }) => {
        if (connection === 'open') {
            console.log('✅ WhatsApp connected');
            const briefing = fs.readFileSync('../briefing.txt', 'utf-8');
            const jid = TO_NUMBER.includes('@s.whatsapp.net')
                ? TO_NUMBER
                : TO_NUMBER + '@s.whatsapp.net';
            await sock.sendMessage(jid, { text: briefing });
            console.log('✅ Briefing sent!');
            process.exit(0);
        }
    });
}

main();
