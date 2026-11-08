import sqlite3
from datetime import datetime, timezone

DB_NAME = "ledger.db"

def init_db():
    """Initialise les tables SQLite et leurs index."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Table des signaux détectés
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            account TEXT NOT NULL,
            tweet_text TEXT NOT NULL,
            token_name TEXT,
            token_symbol TEXT,
            contract_address TEXT,
            price_usd TEXT,
            market_cap TEXT,
            chart_url TEXT,
            tweet_url TEXT UNIQUE
        )
    ''')

    # Table des propositions et votes de la communauté
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            handle TEXT UNIQUE NOT NULL,
            votes_count INTEGER DEFAULT 1,
            discord_message_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_voted_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table pour le cooldown des votes par IP (14 jours)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ip_votes (
            ip_address TEXT PRIMARY KEY,
            last_vote_timestamp DATETIME NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

def save_signal(data):
    """Enregistre un nouveau signal crypto."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        cursor.execute('''
            INSERT INTO signals (
                timestamp, account, tweet_text, token_name, token_symbol,
                contract_address, price_usd, market_cap, chart_url, tweet_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            now_iso, data.get("account"), data.get("tweet_text"), data.get("token_name"),
            data.get("token_symbol"), data.get("contract_address"), data.get("price_usd"),
            data.get("market_cap"), data.get("chart_url"), data.get("tweet_url")
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()

def get_signals_by_period(period='day'):
    """Récupère les signaux stockés selon la période."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if period == 'day':
        query = "SELECT timestamp, account, tweet_text, token_name, token_symbol, contract_address, price_usd, market_cap, chart_url, tweet_url FROM signals WHERE timestamp >= datetime('now', '-1 day') ORDER BY timestamp DESC"
    elif period == 'week':
        query = "SELECT timestamp, account, tweet_text, token_name, token_symbol, contract_address, price_usd, market_cap, chart_url, tweet_url FROM signals WHERE timestamp >= datetime('now', '-7 days') ORDER BY timestamp DESC"
    elif period == 'month':
        query = "SELECT timestamp, account, tweet_text, token_name, token_symbol, contract_address, price_usd, market_cap, chart_url, tweet_url FROM signals WHERE timestamp >= datetime('now', '-30 days') ORDER BY timestamp DESC"
    else:
        query = "SELECT timestamp, account, tweet_text, token_name, token_symbol, contract_address, price_usd, market_cap, chart_url, tweet_url FROM signals ORDER BY timestamp DESC"

    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return rows

def check_ip_cooldown(ip_address):
    """Vérifie le cooldown de 14 jours pour une adresse IP."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT last_vote_timestamp FROM ip_votes WHERE ip_address = ?", (ip_address,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return True, 0

    last_vote = datetime.fromisoformat(row[0])
    elapsed_days = (datetime.now(timezone.utc) - last_vote).total_seconds() / 86400
    if elapsed_days < 14:
        return False, int(14 - elapsed_days)
    return True, 0

def record_ip_vote(ip_address):
    """Enregistre l'horodatage du vote pour une IP."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now_iso = datetime.now(timezone.utc).isoformat()
    cursor.execute('''
        INSERT INTO ip_votes (ip_address, last_vote_timestamp)
        VALUES (?, ?)
        ON CONFLICT(ip_address) DO UPDATE SET last_vote_timestamp = excluded.last_vote_timestamp
    ''', (ip_address, now_iso))
    conn.commit()
    conn.close()

def get_or_create_proposal(handle):
    """Récupère une proposition existante ou en crée une nouvelle."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    handle_clean = handle.lower().lstrip('@')

    cursor.execute("SELECT handle, votes_count, discord_message_id FROM proposals WHERE handle = ?", (handle_clean,))
    row = cursor.fetchone()

    if row:
        new_count = row[1] + 1
        now_iso = datetime.now(timezone.utc).isoformat()
        cursor.execute("UPDATE proposals SET votes_count = ?, last_voted_at = ? WHERE handle = ?", (new_count, now_iso, handle_clean))
        conn.commit()
        conn.close()
        return False, new_count, row[2]
    else:
        cursor.execute("INSERT INTO proposals (handle, votes_count) VALUES (?, 1)", (handle_clean,))
        conn.commit()
        conn.close()
        return True, 1, None

def update_proposal_discord_id(handle, message_id):
    """Associe l'ID d'un message Discord à une proposition."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE proposals SET discord_message_id = ? WHERE handle = ?", (message_id, handle.lower().lstrip('@')))
    conn.commit()
    conn.close()
