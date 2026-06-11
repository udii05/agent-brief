const { makeWASocket, useMultiFileAuthState, fetchLatestBaileysVersion, makeCacheableSignalKeyStore, Browsers } = require('@whiskeysockets/baileys');
const qrcode = require('qrcode-terminal');
const fs = require('fs');
const path = require('path');

const SESSION_PATH = './session';

async function connect(retries = 3) {
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
        generateHighQualityLink: true,
        defaultQueryTimeoutMs: undefined,
    });

    let qrShown = false;

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', ({ qr, connection, lastDisconnect }) => {
        if (qr && !qrShown) {
            qrShown = true;
            qrcode.generate(qr, { small: true });
            console.log('\n📱 Scan QR with WhatsApp > Linked Devices > Link a Device\n');
        }

        if (connection === 'open') {
            console.log('✅ WhatsApp connected!');
            setTimeout(async () => {
                await saveCreds();
                await new Promise(r => setTimeout(r, 2000));

                const files = {};
                function walk(dir) {
                    const entries = fs.readdirSync(dir, { withFileTypes: true });
                    for (const e of entries) {
                        const full = path.join(dir, e.name);
                        const rel = path.relative(SESSION_PATH, full).replace(/\\/g, '/');
                        if (e.isDirectory()) walk(full);
                        else files[rel] = fs.readFileSync(full, 'base64');
                    }
                }
                walk(SESSION_PATH);

                const json = JSON.stringify(files);
                console.log('\n' + '='.repeat(60));
                console.log('✅ WHATSAPP SESSION READY');
                console.log('Size: ' + (json.length / 1024).toFixed(1) + ' KB');
                console.log('='.repeat(60));
                console.log('\nSave this as GitHub secret WHATSAPP_SESSION:\n');
                const b64 = Buffer.from(json).toString('base64');
                console.log(b64);
                console.log('\n' + '='.repeat(60) + '\n');
                process.exit(0);
            }, 3000);
        }

        if (connection === 'close') {
            const statusCode = lastDisconnect?.error?.output?.statusCode;
            const reason = lastDisconnect?.error?.message || 'unknown';
            console.log(`🔌 Disconnected (code: ${statusCode}, reason: ${reason})`);
            if (retries > 0) {
                console.log(`🔄 Reconnecting (${retries} retries left)...`);
                setTimeout(() => connect(retries - 1), 2000);
            } else {
                console.error('❌ Failed to connect after retries. Run setup again.');
                process.exit(1);
            }
        }
    });
}

connect();
