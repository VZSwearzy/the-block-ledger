import os
import requests
from dotenv import load_dotenv

def send_discord_signal(signal: dict):
    """Relaye les alertes détectées sur le canal Discord via webhook."""
    load_dotenv(override=True)
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()

    if not webhook_url:
        return

    account = signal.get("account", "Unknown")
    text = signal.get("tweet_text", "")
    token_name = signal.get("token_name") or "Detected Token"
    symbol = signal.get("token_symbol") or "N/A"
    price = signal.get("price_usd") or "N/A"
    mcap = signal.get("market_cap") or "N/A"
    ca = signal.get("contract_address")
    chart_url = signal.get("chart_url")
    tweet_url = signal.get("tweet_url", f"https://x.com/{account}")

    try:
        formatted_mcap = f"${float(mcap):,.0f}"
    except Exception:
        formatted_mcap = f"${mcap}" if mcap != "N/A" else "N/A"

    embed = {
        "title": f"Dispatch Detected — @{account}",
        "url": tweet_url,
        "color": 0x2563EB,
        "description": f"*{text[:280]}...*" if len(text) > 280 else f"*{text}*",
        "fields": [
            {
                "name": "Token",
                "value": f"**{token_name}** (`${symbol}`)",
                "inline": True
            },
            {
                "name": "Price USD",
                "value": f"`${price}`",
                "inline": True
            },
            {
                "name": "Market Cap",
                "value": f"`{formatted_mcap}`",
                "inline": True
            }
        ],
        "footer": {
            "text": "The Block Ledger • Market Intelligence"
        }
    }

    if ca:
        embed["fields"].append({
            "name": "Contract Address (CA)",
            "value": f"`{ca}`",
            "inline": False
        })

    if chart_url:
        embed["fields"].append({
            "name": "Chart Link",
            "value": f"[Open DexScreener ↗]({chart_url})",
            "inline": False
        })

    payload = {
        "username": "The Block Ledger",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/2965/2965879.png",
        "embeds": [embed]
    }

    try:
        res = requests.post(webhook_url, json=payload, timeout=8)
        if res.status_code in [200, 204]:
            print(f"[Discord] Signal relayé pour @{account}")
        else:
            print(f"[Discord] Code retour inattendu: {res.status_code}")
    except Exception as e:
        print(f"[Discord] Erreur de transmission: {e}")
