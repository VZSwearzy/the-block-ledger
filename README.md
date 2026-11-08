# The Block Ledger

> High-frequency decentralized intelligence terminal & contract radar for the Solana ecosystem.

---

## Overview

**The Block Ledger** is an automated on-chain intelligence pipeline. It continuously indexes social signals, extracts Solana contract addresses (CAs) and cashtags via headless scraping workers, enriches raw market data with DexScreener metrics, and broadcasts validated dispatches in real-time.

---

## Architecture & Tech Stack

- **Backend**: Python 3.11+, Flask (REST API & SSR)
- **Database**: SQLite (optimized with local persistence)
- **Scraping Engine**: Playwright (Headless Chromium workers)
- **Enrichment**: DexScreener Public API
- **Community & Automation**: Discord Webhooks & Ticket Tool RBAC

---

## Quick Start (Local Setup)

### 1. Clone & Environment Setup

git clone https://github.com/VZSwearzy/the-block-ledger.git
cd the-block-ledger
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

### 2. Configuration

Copy the template and configure your environment variables:
cp .env.example .env

Fill in the following keys inside `.env`:
PORT=8080
DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
DISCORD_SUGGESTIONS_WEBHOOK_URL="https://discord.com/api/webhooks/..."
DISCORD_INVITE_URL="https://discord.gg/..."
TERMINAL_MODE="public"

### 3. Run the Terminal

Start the Flask web server:
python app.py

In a separate terminal, launch the autonomous radar engine:
python radar.py

Access the terminal dashboard at http://localhost:8080.

---

## Security & Governance

- **Rate Limiting**: Sybil-resistant voting pipeline with a 14-day IP cooldown window.
- **Role Isolation**: Strict Discord RBAC with ticket-based verification for node supporters.
- **Data Privacy**: No credentials, session state cookies, or local databases are tracked in version control.

---

## License

MIT License. Open-source research tool.
