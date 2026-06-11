# Agent Brief 🤖📬

Daily AI briefing delivered to your WhatsApp at 8AM IST.

Fetches news from RSS feeds + NewsAPI, summarizes with Google Gemini, and sends via WhatsApp.

## Setup

### 1. Prerequisites
- Python 3.11+
- Node.js 18+
- WhatsApp account

### 2. API Keys

| Key | Where to get it |
|---|---|
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey |
| `NEWSAPI_KEY` | https://newsapi.org/register (Developer plan) |

### 3. WhatsApp Session (one-time)

```bash
cd whatsapp
npm install
node setup.js
```

A QR code appears in the terminal. Open WhatsApp on your phone → Linked Devices → Link a Device and scan it. A base64 session string will be printed — copy it.

### 4. GitHub Secrets

Add these to your repo: **Settings → Secrets and variables → Actions**

| Secret | Value |
|---|---|
| `GEMINI_API_KEY` | Your Gemini API key |
| `NEWSAPI_KEY` | Your NewsAPI key |
| `WHATSAPP_SESSION` | Base64 string from step 3 |
| `TO_NUMBER` | Your WhatsApp number (e.g. `919876543210` — no `+` or spaces) |

### 5. Test Locally

```bash
pip install -r requirements.txt
# Create .env with the 4 keys above
set GEMINI_API_KEY=your_key
set NEWSAPI_KEY=your_key
set WHATSAPP_SESSION=your_session
set TO_NUMBER=your_number
python main.py
cd whatsapp && node index.js
```

### 6. Push to GitHub

Push to `main` — the workflow runs daily at 8AM IST. You can also trigger it manually from the Actions tab.

## How It Works

```
8AM IST → GitHub Actions cron
    │
    ├── main.py (Python)
    │   ├── RSS + NewsAPI → articles
    │   ├── Gemini → summarized briefing
    │   └── briefing.txt
    │
    └── whatsapp/index.js (Node)
        ├── whatsapp-web.js → restore session
        └── Send briefing → Your WhatsApp 📱
```

## Session Expiry

WhatsApp sessions expire every few weeks. You'll get an auth failure in the workflow — just re-run `node setup.js` locally and update the `WHATSAPP_SESSION` secret.

## Tech Stack

- **News**: RSS (TechCrunch, arXiv, HN) + NewsAPI
- **AI**: Google Gemini 2.0 Flash
- **Delivery**: whatsapp-web.js
- **Schedule**: GitHub Actions cron
