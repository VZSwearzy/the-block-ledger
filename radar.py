import os
import json
import re
import random
import asyncio
import httpx
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from database import init_db, save_signal
from discord_alerts import send_discord_signal

load_dotenv()

KEYWORDS = [
    "ca", "contract", "pump", "dex", "solana", "sol",
    "mint", "launch", "presale", "airdrop", "moon", "buy", "holding"
]

MAJOR_TOKENS = {"BTC", "ETH", "SOL", "USDT", "USDC", "BNB", "WBTC", "ENA"}
MIN_LIQUIDITY_USD = 2500

def load_config():
    """Charge les comptes cibles et l'intervalle de scan."""
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except Exception:
        return {
            "target_accounts": ["blknoiz06", "muststopmurad", "theunipcs", "lookonchain"],
            "scan_interval_seconds": 45
        }

def load_x_cookies():
    """Charge les cookies d'authentification depuis le .env."""
    load_dotenv(override=True)
    auth_token = os.getenv("X_AUTH_TOKEN")
    ct0 = os.getenv("X_CT0")
    if auth_token and ct0:
        return [
            {"name": "auth_token", "value": auth_token, "domain": ".x.com", "path": "/", "secure": True},
            {"name": "ct0", "value": ct0, "domain": ".x.com", "path": "/", "secure": True}
        ]
    return []

def extract_signals(text: str):
    """Extrait cashtags, adresses Solana en base58 et mots-clés."""
    cashtags = [t.upper() for t in re.findall(r"\$([a-zA-Z0-9_]{2,10})", text)]
    addresses = re.findall(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b", text)
    words = set(re.findall(r"\w+", text.lower()))
    has_keywords = any(kw in words for kw in KEYWORDS)
    memecoin_tags = [t for t in cashtags if t not in MAJOR_TOKENS]
    return memecoin_tags, list(set(addresses)), has_keywords

async def get_dexscreener_info(client: httpx.AsyncClient, query: str):
    """Requête asynchrone non-bloquante vers l'API DexScreener."""
    try:
        url = f"https://api.dexscreener.com/latest/dex/search?q={query}"
        res = await client.get(url, timeout=6.0)
        if res.status_code != 200:
            return None
        pairs = res.json().get("pairs", [])
        if pairs:
            valid_pairs = [p for p in pairs if float(p.get("liquidity", {}).get("usd", 0) or 0) >= MIN_LIQUIDITY_USD]
            best = max(valid_pairs if valid_pairs else pairs, key=lambda p: float(p.get("liquidity", {}).get("usd", 0) or 0))
            base = best.get("baseToken", {})
            return {
                "name": base.get("name", "Unknown"),
                "symbol": base.get("symbol", ""),
                "price": str(best.get("priceUsd", "N/A")),
                "mcap": str(best.get("marketCap", best.get("fdv", "N/A"))),
                "url": best.get("url", "")
            }
    except Exception:
        pass
    return None

async def check_account(page, client: httpx.AsyncClient, username: str, seen_ids: set):
    """Scrape la timeline d'un compte cible."""
    url = f"https://x.com/{username}"
    print(f" Scanning: @{username}...")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=25000)
        await asyncio.sleep(1.5)
        await page.mouse.wheel(0, random.randint(250, 400))

        try:
            await page.wait_for_selector('article', timeout=8000)
        except Exception:
            return

        articles = await page.query_selector_all('article')
        if not articles:
            return

        for article in articles[:5]:
            tweet_url = url
            links = await article.query_selector_all('a[href*="/status/"]')
            for link in links:
                href = await link.get_attribute('href')
                if href and "/status/" in href:
                    tweet_url = f"https://x.com{href}" if not href.startswith('http') else href
                    break

            text_el = await article.query_selector('div[data-testid="tweetText"]')
            if not text_el:
                continue

            raw_text = (await text_el.inner_text()).strip()
            tweet_id = tweet_url if "/status/" in tweet_url else f"{username}_{hash(raw_text)}"

            if tweet_id in seen_ids:
                continue

            seen_ids.add(tweet_id)
            cashtags, addresses, has_keywords = extract_signals(raw_text)

            if cashtags or addresses or has_keywords:
                search_query = addresses[0] if addresses else (cashtags[0] if cashtags else None)
                dex = await get_dexscreener_info(client, search_query) if search_query else None

                signal_data = {
                    "account": username,
                    "tweet_text": raw_text,
                    "token_name": dex["name"] if dex else None,
                    "token_symbol": dex["symbol"] if dex else (cashtags[0] if cashtags else None),
                    "contract_address": addresses[0] if addresses else None,
                    "price_usd": dex["price"] if dex else None,
                    "market_cap": dex["mcap"] if dex else None,
                    "chart_url": dex["url"] if dex else None,
                    "tweet_url": tweet_url
                }

                save_signal(signal_data)
                send_discord_signal(signal_data)
                print(f"Indexé & Relayé: @{username}")

    except Exception as e:
        print(f" [@{username}] {e.__class__.__name__}")

async def run_tracker():
    """Boucle principale du radar."""
    init_db()
    cookies = load_x_cookies()
    if not cookies:
        print("Cookies manquants. Lance setup_auth.py ou synchronise via le dashboard.")
        return

    seen_ids = set()
    sweep_count = 0
    print("The Block Ledger Radar démarré...")

    async with httpx.AsyncClient() as http_client:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            await context.add_cookies(cookies)
            page = await context.new_page()

            while True:
                config = load_config()
                accounts = list(config.get("target_accounts", []))
                base_interval = config.get("scan_interval_seconds", 45)

                random.shuffle(accounts)

                for acc in accounts:
                    await check_account(page, http_client, acc, seen_ids)
                    await asyncio.sleep(random.uniform(2.5, 4.5))

                sweep_count += 1
                # Recyclage de l'onglet tous les 15 cycles pour purger la mémoire DOM
                if sweep_count % 15 == 0:
                    await page.close()
                    page = await context.new_page()

                jitter_interval = random.uniform(base_interval * 0.9, base_interval * 1.25)
                print(f"⏳ Pause de {int(jitter_interval)}s avant le prochain sweep...")
                await asyncio.sleep(jitter_interval)

if __name__ == "__main__":
    asyncio.run(run_tracker())
