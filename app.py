import os
import json
import requests
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
from dotenv import load_dotenv
from database import (
    init_db, get_signals_by_period, check_ip_cooldown,
    record_ip_vote, get_or_create_proposal, update_proposal_discord_id
)

load_dotenv()

app = Flask(__name__)
init_db()

def load_config():
    """Charge la configuration depuis config.json."""
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except Exception:
        return {
            "target_accounts": ["blknoiz06", "muststopmurad", "theunipcs", "lookonchain"],
            "scan_interval_seconds": 45
        }

def save_config(data):
    """Sauvegarde la configuration (désactivé si APP_MODE est public)."""
    if os.getenv("APP_MODE", "personal") == "public":
        return
    with open("config.json", "w") as f:
        json.dump(data, f, indent=2)

@app.template_filter('format_date')
def format_date_filter(date_str, period='day'):
    """Formate les timestamps ISO pour l'affichage."""
    if not date_str:
        return ""
    try:
        dt = datetime.fromisoformat(date_str)
        if period == 'day':
            return dt.strftime("%H:%M")
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return date_str

@app.route('/')
def index():
    load_dotenv(override=True)
    discord_url = os.getenv("DISCORD_INVITE_URL", "https://discord.gg/")
    github_url = os.getenv("GITHUB_REPO_URL", "https://github.com/")
    donate_sol = os.getenv("DONATE_SOL_ADDRESS", "")
    app_mode = os.getenv("APP_MODE", "personal")

    period = request.args.get('period', 'day')
    signals = get_signals_by_period(period)
    config = load_config()
    accounts = config.get("target_accounts", [])

    is_authenticated = bool(os.getenv("X_AUTH_TOKEN") and os.getenv("X_CT0"))

    return render_template(
        'index.html',
        signals=signals,
        accounts=accounts,
        active_period=period,
        is_authenticated=is_authenticated,
        app_mode=app_mode,
        discord_url=discord_url,
        github_url=github_url,
        donate_sol=donate_sol
    )

@app.route('/api/signals')
def api_signals():
    """Endpoint pour le rafraîchissement dynamique du flux."""
    period = request.args.get('period', 'day')
    signals = get_signals_by_period(period)
    data = []
    for s in signals:
        data.append({
            "date": s[0],
            "formatted_date": format_date_filter(s[0], period),
            "account": s[1],
            "tweet_text": s[2],
            "token_name": s[3] or "",
            "token_symbol": s[4] or "",
            "contract_address": s[5] or "",
            "price_usd": s[6] or "N/A",
            "market_cap": s[7] or "N/A",
            "chart_url": s[8] or "",
            "tweet_url": s[9] or "#"
        })
    return jsonify(data)

@app.route('/api/submit-proposal', methods=['POST'])
def submit_proposal():
    """Gestion des propositions de la communauté et synchronisation Discord."""
    load_dotenv(override=True)
    webhook_url = os.getenv("DISCORD_SUGGESTIONS_WEBHOOK_URL") or os.getenv("DISCORD_WEBHOOK_URL")

    if not webhook_url:
        return jsonify({"success": False, "message": "Webhook Discord non configuré."}), 500

    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if client_ip and ',' in client_ip:
        client_ip = client_ip.split(',')[0].strip()

    can_vote, remaining_days = check_ip_cooldown(client_ip)
    if not can_vote:
        return jsonify({
            "success": False,
            "message": f"Vote déjà effectué. Prochain vote dans {remaining_days} jour(s)."
        }), 429

    data = request.get_json() or {}
    handle = data.get("handle", "").strip().lstrip("@")

    if not handle or len(handle) > 30:
        return jsonify({"success": False, "message": "Handle X invalide."}), 400

    is_new, vote_count, discord_msg_id = get_or_create_proposal(handle)

    embed = {
        "title": "🗳️ Community Pool Proposal",
        "description": f"Target Account: **[@{handle}](https://x.com/{handle})**",
        "color": 0x2563eb,
        "fields": [
            {"name": "Community Votes", "value": f"**{vote_count}** 👍", "inline": True},
            {"name": "Status", "value": "Under Consideration", "inline": True}
        ],
        "footer": {"text": "The Block Ledger • 1 vote every 14 days"}
    }

    try:
        if is_new or not discord_msg_id:
            post_url = f"{webhook_url}?wait=true"
            res = requests.post(post_url, json={"embeds": [embed]}, timeout=5)
            if res.status_code in [200, 201]:
                msg_data = res.json()
                msg_id = msg_data.get("id")
                if msg_id:
                    update_proposal_discord_id(handle, msg_id)
        else:
            patch_url = f"{webhook_url}/messages/{discord_msg_id}"
            requests.patch(patch_url, json={"embeds": [embed]}, timeout=5)

        record_ip_vote(client_ip)
        return jsonify({
            "success": True,
            "message": f"Vote enregistré pour @{handle} ! Total des votes : {vote_count}."
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Erreur de relais : {str(e)}"}), 500

@app.route('/add-account', methods=['POST'])
def add_account():
    """Ajoute un compte cible à la configuration."""
    if os.getenv("APP_MODE", "personal") == "public":
        return redirect(url_for('index'))
    account = request.form.get('account', '').strip().lstrip('@')
    if account:
        config = load_config()
        if account not in config.get("target_accounts", []):
            config.setdefault("target_accounts", []).append(account)
            save_config(config)
    return redirect(url_for('index'))

@app.route('/remove-account/<account>')
def remove_account(account):
    """Supprime un compte cible de la configuration."""
    if os.getenv("APP_MODE", "personal") == "public":
        return redirect(url_for('index'))
    config = load_config()
    accounts = config.get("target_accounts", [])
    if account in accounts:
        accounts.remove(account)
        config["target_accounts"] = accounts
        save_config(config)
    return redirect(url_for('index'))

@app.route('/api/auth/sync-browser', methods=['POST'])
def sync_browser():
    """Synchronise la session active du navigateur local."""
    if os.getenv("APP_MODE", "personal") == "public":
        return jsonify({"message": "Action non autorisée en mode public."}), 403
    try:
        from setup_auth import extract_and_save_tokens
        success, msg = extract_and_save_tokens()
        if success:
            return jsonify({"message": msg}), 200
        return jsonify({"message": msg}), 400
    except Exception as e:
        return jsonify({"message": f"Erreur: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
