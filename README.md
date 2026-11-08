# The Block Ledger ⚡

[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-Flask-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Scraper](https://img.shields.io/badge/scraping-Playwright-green.svg)](https://playwright.dev/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> Autonomous on-chain intelligence pipeline & contract discovery terminal for the Solana ecosystem.

---

## Overview

**The Block Ledger** is an automated market surveillance daemon designed to index low-latency alpha signals across targeted social channels. It monitors specified key opinion leaders (KOLs), extracts Solana contract addresses (`base58`) and cashtags, cross-references liquidity metrics through DexScreener, and broadcasts real-time structured dispatches via Discord webhooks and an integrated web terminal.

---

## System Architecture

```text
       ┌───────────────┐
       │ Target KOLs   │ (X / Twitter Profiles)
       └───────┬───────┘
               │  [Playwright Headless Engine]
               ▼
       ┌───────────────┐
       │   radar.py    │ ───► Regex Extraction (CA & Cashtags)
       └───────┬───────┘
               │  [Async HTTPX Queries]
               ▼
       ┌───────────────┐
       │  DexScreener  │ ───► Price, Market Cap & Liquidity Validation
       └───────┬───────┘
               │
       ┌───────┴───────┐
       ▼               ▼
┌─────────────┐ ┌───────────────┐
│  ledger.db  │ │ discord_alerts│
│  (SQLite3)  │ │ (Live Webhook)│
└──────┬──────┘ └───────────────┘
       │
       ▼
┌─────────────┐
│   app.py    │ (Flask REST API & Live Terminal Dashboard)
└─────────────┘
```

---

## Features

- **Asynchronous Scraping Engine**: Headless Chromium runner with automated session rotation, DOM recycling, and adaptive jitter to bypass basic anti-bot patterns.
- **On-Chain Signal Extraction**: Regex filtering targeting Solana contract addresses (`32-44` alphanumeric base58 chars) and token cashtags, automatically excluding major market pairs ($BTC, $ETH, $SOL).
- **Automated Metric Enrichment**: Fetches live pairs, volume, price, and FDV/market cap from DexScreener before dispatch.
- **Discord Dispatch Relay**: Rich embeds containing token metadata, instant DexScreener links, and contract addresses.
- **Local Surveillance Terminal**: Lightweight Flask dashboard with dynamic polling and community proposal voting (IP-based cooldown rate limiting).

---

## Quick Start (Local Setup)

### 1. Clone & Environment Setup

```bash
git clone https://github.com/VZSwearzy/the-block-ledger.git
cd the-block-ledger
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Configuration

Copy the template environment file:

```bash
cp .env.example .env
```

Populate the required keys inside `.env`:

```env
PORT=8080
APP_MODE=personal
DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/your/webhook/url"
DISCORD_SUGGESTIONS_WEBHOOK_URL=""
DISCORD_INVITE_URL="https://discord.gg/"
GITHUB_REPO_URL="https://github.com/"
DONATE_SOL_ADDRESS=""

# X Session Credentials (extract from browser DevTools -> Application -> Cookies)
X_AUTH_TOKEN="your_auth_token_here"
X_CT0="your_ct0_here"
```

Configure target watchlist profiles and scan frequency inside `config.json`:

```json
{
  "max_tweet_age_minutes": 15,
  "scan_interval_seconds": 45,
  "target_accounts": [
    "blknoiz06",
    "muststopmurad",
    "theunipcs",
    "lookonchain"
  ]
}
```

### 3. Run the Terminal

Start the Flask web server:

```bash
python3 app.py
```

In a separate terminal tab, launch the autonomous radar engine:

```bash
source venv/bin/activate
python3 radar.py
```

Access the terminal dashboard at `http://localhost:8080`.

---

## Security & Ethics

- **Zero Hardcoded Secrets**: All authentication keys and webhooks are strictly decoupled via `.env`.
- **Local Persistence**: Database files (`ledger.db`) are excluded from tracking.
- **Rate Limiting**: Community endpoints utilize a 14-day client-side IP cooldown window.

---

## License

This project is licensed under the [MIT License](LICENSE).
