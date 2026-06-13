const { makeWASocket, useMultiFileAuthState, fetchLatestBaileysVersion, makeCacheableSignalKeyStore, Browsers, DisconnectReason } = require('@whiskeysockets/baileys');
const fs = require('fs');
const path = require('path');
const pino = require('pino');

const MAX_MESSAGE_SIZE = 65000; // WhatsApp text limit ~65KB
const SESSION_PATH = './session';
const SESSION_B64 = process.env.WHATSAPP_SESSION;
const RAW_NUMBER = process.env.TO_NUMBER || '';

if (!RAW_NUMBER) {
    console.error('Missing TO_NUMBER env var');
    process.exit(1);
}
if (!SESSION_B64) {
    console.error('Missing WHATSAPP_SESSION env var');
    process.exit(1);
}

// Normalize: strip +, spaces, dashes, parens
const CLEAN_NUMBER = RAW_NUMBER.replace(/[\s\-\+\(\)]/g, '');
const JID = CLEAN_NUMBER.includes('@') ? CLEAN_NUMBER : CLEAN_NUMBER + '@s.whatsapp.net';

function maskJid(jid) {
    const atIdx = jid.indexOf('@');
    if (atIdx === -1) return jid;
    const local = jid.slice(0, atIdx);
    if (local.length <= 6) return local.slice(0, 2) + '****' + '@' + jid.slice(atIdx + 1);
    return local.slice(0, 3) + '****' + local.slice(-3) + '@' + jid.slice(atIdx + 1);
}

console.log('TO_NUMBER raw length:', RAW_NUMBER.length);
console.log('TO_NUMBER cleaned length:', CLEAN_NUMBER.length);
console.log('Target JID:', maskJid(JID));

function logSessionDiagnostics() {
    const sessionDir = path.resolve(SESSION_PATH);
    if (!fs.existsSync(sessionDir)) {
        console.log('Session directory does not exist');
        return;
    }
    const items = fs.readdirSync(sessionDir, { withFileTypes: true });
    let fileCount = 0;
    let totalSize = 0;
    function walk(dir) {
        const entries = fs.readdirSync(dir, { withFileTypes: true });
        for (const e of entries) {
            const full = path.join(dir, e.name);
            if (e.isDirectory()) walk(full);
            else {
                fileCount++;
                totalSize += fs.statSync(full).size;
            }
        }
    }
    walk(sessionDir);
    console.log(`Session dir: ${fileCount} files, ${(totalSize / 1024).toFixed(1)} KB`);

    const credsPath = path.join(sessionDir, 'creds.json');
    if (fs.existsSync(credsPath)) {
        try {
            const creds = JSON.parse(fs.readFileSync(credsPath, 'utf-8'));
            const registeredId = creds?.me?.id || 'unknown';
            const registrationId = creds?.registrationId || 'N/A';
            const serverToken = creds?.serverToken ? creds.serverToken.slice(0, 16) + '...' : 'N/A';
            console.log(`Registered ID: ${registeredId}`);
            console.log(`Registration ID: ${registrationId}`);
            console.log(`Server token: ${serverToken}`);
        } catch (e) {
            console.log('Could not parse creds.json:', e.message);
        }
    } else {
        console.log('No creds.json found');
    }
}

async function main() {
    // Check if session files already exist (restored from cache)
    const credsPath = path.join(SESSION_PATH, 'creds.json');
    if (!fs.existsSync(credsPath)) {
        console.log('No cached session found, decoding from secret...');
        try {
            const raw = Buffer.from(SESSION_B64, 'base64').toString();
            const files = JSON.parse(raw);
            console.log('Session entries:', Object.keys(files).length);
            for (const [relPath, content] of Object.entries(files)) {
                const fullPath = path.join(SESSION_PATH, relPath);
                fs.mkdirSync(path.dirname(fullPath), { recursive: true });
                fs.writeFileSync(fullPath, Buffer.from(content, 'base64'));
            }
        } catch (e) {
            console.error('Failed to decode WHATSAPP_SESSION:', e.message);
            process.exit(1);
        }
    } else {
        console.log('Using cached session from previous run');
    }

    logSessionDiagnostics();

    const { state, saveCreds } = await useMultiFileAuthState(SESSION_PATH);
    const { version } = await fetchLatestBaileysVersion();
    const logger = pino({ level: 'warn' });

    const sock = makeWASocket({
        version,
        browser: Browsers.windows('Chrome'),
        auth: {
            creds: state.creds,
            keys: makeCacheableSignalKeyStore(state.keys),
        },
        syncFullHistory: false,
        markOnlineOnConnect: true,
        logger,
    });

    let deliveryReceived = false;

    sock.ev.on('creds.update', async () => {
        await saveCreds();
    });

    // Track message delivery
    sock.ev.on('messages.upsert', async ({ messages }) => {
        for (const msg of messages) {
            if (msg.key?.fromMe && msg.key?.id) {
                console.log('Delivery receipt for message:', msg.key.id);
                console.log('Status:', msg.status);
                // status 2 = read, 1 = delivered, 0 = error
                if (msg.status >= 1) {
                    deliveryReceived = true;
                }
            }
        }
    });

    sock.ev.on('messages.update', async (updates) => {
        for (const update of updates) {
            if (update.key?.fromMe && update.update?.status !== undefined) {
                console.log('Message status update:', update.key.id, '-> status', update.update.status);
                if (update.update.status >= 1) {
                    deliveryReceived = true;
                }
            }
        }
    });

    const connectionTimeout = setTimeout(() => {
        console.error('Timed out waiting for connection (30s)');
        process.exit(1);
    }, 30000);

    sock.ev.on('connection.update', async ({ connection, lastDisconnect }) => {
        console.log('Connection state:', connection);

        if (connection === 'open') {
            clearTimeout(connectionTimeout);

            // Log the connected account's own JID
            const myJid = sock.user?.id;
            console.log('WhatsApp connected');
            console.log('Logged-in as:', myJid ? maskJid(myJid) : 'unknown');
            console.log('Target JID:', maskJid(JID));

            // Check if logged-in account matches target
            if (myJid) {
                const myClean = myJid.split(':')[0].replace(/[\s\-\+\(\)]/g, '');
                const targetClean = CLEAN_NUMBER;
                const match = myClean.includes(targetClean) || targetClean.includes(myClean);
                console.log('Sender-to-target match:', match ? 'YES (self-send)' : 'NO (different accounts?)');
                if (!match) {
                    console.warn('WARNING: Your WhatsApp account JID does not contain TO_NUMBER.');
                    console.warn('You might be sending to a different number than your own!');
                }
            }

            // Check briefing exists
            const briefingPath = path.join(__dirname, '..', 'briefing.txt');
            if (!fs.existsSync(briefingPath)) {
                console.error('briefing.txt not found at', briefingPath);
                await saveCreds();
                process.exit(1);
            }

            try {
                const briefing = fs.readFileSync(briefingPath, 'utf-8');
                if (!briefing.trim()) {
                    console.error('briefing.txt is empty');
                    await saveCreds();
                    process.exit(1);
                }

                let byteLen = Buffer.byteLength(briefing, 'utf-8');
                console.log('Briefing size:', (byteLen / 1024).toFixed(1), 'KB');

                let textToSend = briefing;
                if (byteLen > MAX_MESSAGE_SIZE) {
                    console.error(`Briefing too large (${byteLen} bytes > ${MAX_MESSAGE_SIZE} limit). Truncating...`);
                    textToSend = briefing.slice(0, MAX_MESSAGE_SIZE - 100);
                    byteLen = Buffer.byteLength(textToSend, 'utf-8');
                }

                console.log(`Sending to ${maskJid(JID)} (${(byteLen / 1024).toFixed(1)} KB)...`);

                const sent = await sock.sendMessage(JID, { text: textToSend });
                const msgId = sent?.key?.id || 'unknown';
                console.log('Message ID:', msgId);
                console.log('Message sent to WhatsApp server');

                // Wait for delivery receipts (up to 15s)
                for (let i = 0; i < 15; i++) {
                    await new Promise(r => setTimeout(r, 1000));
                    if (deliveryReceived) {
                        console.log('Delivery confirmed!');
                        break;
                    }
                }

                if (!deliveryReceived) {
                    console.warn('No delivery receipt received within 15s timeout.');
                    console.warn('The message was sent to WhatsApp servers but delivery not confirmed.');
                    console.warn('Possible causes: wrong JID, number not on WhatsApp, or silent drop.');
                }
            } catch (err) {
                console.error('Send failed:', err.message);
                if (err.stack) console.error(err.stack.split('\n').slice(0, 3).join('\n'));
            }

            // Save updated creds before exiting
            await saveCreds();
            process.exit(deliveryReceived ? 0 : 0); // Exit 0 for now, log only
        }

        if (connection === 'close') {
            clearTimeout(connectionTimeout);
            const err = lastDisconnect?.error;
            const statusCode = err?.output?.statusCode;
            const reason = err?.message || err?.toString() || 'unknown';

            // Map Baileys disconnect reasons
            let humanReason = reason;
            if (statusCode === DisconnectReason.loggedOut) humanReason = 'Logged Out (401) — session expired, needs re-auth';
            else if (statusCode === DisconnectReason.badSession) humanReason = 'Bad Session (500) — corrupted/invalid session data';
            else if (statusCode === DisconnectReason.connectionClosed) humanReason = 'Connection Closed (428)';
            else if (statusCode === DisconnectReason.connectionLost) humanReason = 'Connection Lost (408)';
            else if (statusCode === DisconnectReason.connectionReplaced) humanReason = 'Connection Replaced (440) — another client connected with this session';
            else if (statusCode === DisconnectReason.forbidden) humanReason = 'Forbidden (403)';
            else if (statusCode === DisconnectReason.restartRequired) humanReason = 'Restart Required (515)';
            else if (statusCode === DisconnectReason.unavailableService) humanReason = 'Service Unavailable (503)';
            else if (statusCode === DisconnectReason.timedOut) humanReason = 'Timed Out (408)';
            else if (statusCode === DisconnectReason.multideviceMismatch) humanReason = 'Multi-device Mismatch (411)';

            console.error('Connection closed.');
            console.error('Status code:', statusCode);
            console.error('Reason:', reason);
            console.error('Human readable:', humanReason);

            // Check if it's a recoverable disconnect
            const isLoggedOut = statusCode === DisconnectReason.loggedOut || statusCode === DisconnectReason.badSession;
            if (isLoggedOut) {
                console.error('Session appears to be invalid/expired. Run `npm run setup` to generate a new session.');
            }

            // Try to save creds before dying
            try { await saveCreds(); } catch (_) { /* ignore */ }
            process.exit(1);
        }
    });
}

main();
