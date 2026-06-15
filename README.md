<div align="center">

<img src="assets/logo.svg" alt="Agent Brief" width="260" />

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Node](https://img.shields.io/badge/Node-22+-5FA04E?logo=node.js&logoColor=white)](https://nodejs.org)
[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-daily-2088FF?logo=githubactions&logoColor=white)](../../actions/workflows/daily-briefing.yml)
[![License](https://img.shields.io/badge/License-MIT-F05032?logo=opensourceinitiative&logoColor=white)](LICENSE)

<p><em>Automated daily briefing covering AI/ML and Agentic AI developments. Delivered to your WhatsApp every morning.</em></p>

</div>

---

## Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
  - [API Keys](#1-api-keys)
  - [WhatsApp Session](#2-whatsapp-session)
  - [GitHub Secrets](#3-github-secrets)
  - [Local Testing](#4-local-testing)
- [Deployment](#deployment)
- [Session Maintenance](#session-maintenance)
- [Tech Stack](#tech-stack)

---

## Architecture

```
[GitHub Actions Cron] -- 08:00 IST
       |
       +-- main.py (Python)
       |     +-- NewsAPI + RSS Feeds --> raw articles
       |     +-- Google Gemini --> summarised briefing
       |     +-- briefing.txt
       |
       +-- whatsapp/index.js (Node.js)
             +-- @whiskeysockets/baileys --> restore session
             +-- Send briefing --> your WhatsApp
```

The pipeline is orchestrated by a GitHub Actions scheduled workflow. The Python layer handles content acquisition and generation; the Node.js layer handles WhatsApp delivery using the Baileys library (WhatsApp Web protocol).

---

## Prerequisites

- Python 3.11 or later
- Node.js 22 or later
- An active WhatsApp account

---

## Setup

### 1. API Keys

| Key | Provider | Registration |
|---|---|---|
| `GEMINI_API_KEY` | Google AI Studio | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `NEWSAPI_KEY` | NewsAPI | [newsapi.org/register](https://newsapi.org/register) (Developer plan) |

### 2. WhatsApp Session

WhatsApp requires an authenticated session to send messages. This is a one-time setup step that links your WhatsApp account via QR code.

```bash
cd whatsapp
npm install
node setup.js
```

A QR code will be printed in the terminal. Open **WhatsApp** on your phone, navigate to **Settings > Linked Devices > Link a Device**, and scan the QR code. A base64-encoded session string will be printed to the terminal.

Copy the entire base64 string -- it will be stored as the `WHATSAPP_SESSION` secret in GitHub.

### 3. GitHub Secrets

Navigate to your repository on GitHub: **Settings > Secrets and variables > Actions**. Add the following secrets:

| Secret | Description |
|---|---|
| `GEMINI_API_KEY` | Your Google Gemini API key |
| `NEWSAPI_KEY` | Your NewsAPI key |
| `WHATSAPP_SESSION` | Base64 session string generated in the previous step |
| `TO_NUMBER` | Your WhatsApp number in full international format (e.g. `919876543210`). Do not include `+`, spaces, or dashes. |

### 4. Local Testing

Create a `.env` file in the project root with the same four keys listed above. Run the pipeline end-to-end:

```bash
pip install -r requirements.txt
python main.py
cd whatsapp && node index.js
```

The first command generates `briefing.txt`; the second sends it via WhatsApp.

---

## Deployment

Push the repository to GitHub. The workflow defined in `.github/workflows/daily-briefing.yml` executes automatically at **08:00 IST** each day. You can also trigger a manual run from the **Actions** tab in the repository.

The workflow performs the following steps:

1. Checks out the repository
2. Sets up Python 3.11 and installs dependencies
3. Runs `main.py` to generate the briefing
4. Uploads the briefing as a build artifact
5. Sets up Node.js 22 and installs dependencies
6. Restores the cached WhatsApp session
7. Sends the briefing via `node whatsapp/index.js`
8. Persists the updated session back to the cache for subsequent runs

---

## Session Maintenance

WhatsApp sessions can expire after extended periods of inactivity. When a session expires, the workflow will log an error with the message *"Logged Out (401) -- session expired, needs re-auth"*.

To resolve this, re-authenticate by running the setup steps locally:

```bash
cd whatsapp
node setup.js
```

Replace the `WHATSAPP_SESSION` secret in GitHub with the newly generated base64 string.

---

## Tech Stack

| Layer | Technology |
|---|---|
| News aggregation | NewsAPI, RSS (TechCrunch, arXiv, Hacker News) |
| AI summarisation | Google Gemini 2.0 Flash |
| WhatsApp delivery | [@whiskeysockets/baileys](https://github.com/WhiskeySockets/Baileys) |
| Scheduling | GitHub Actions (cron) |
| Runtime | Python 3.11, Node.js 22 |

---

## License

[MIT](LICENSE)

---

Udita Chakraborty
<p align="left"> <a href="https://github.com/udii05"> <img src="https://img.shields.io/badge/GitHub-udii05-black?style=flat-square&logo=github"> </a> <a href="https://www.linkedin.com/in/udita-chakraborty-b890982a2/"> <img src="https://img.shields.io/badge/LinkedIn-Udita%20Chakraborty-blue?style=flat-square&logo=linkedin"> </a> <a href="https://www.instagram.com/u_dii05"> <img src="https://img.shields.io/badge/Instagram-@u_dii05-e84393?style=flat-square&logo=instagram"> </a> </p>
