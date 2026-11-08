import os
import browser_cookie3
from dotenv import set_key

ENV_PATH = ".env"

def update_env(auth_token: str, ct0: str):
    """Enregistre les tokens extraits dans le fichier .env."""
    if not os.path.exists(ENV_PATH):
        with open(ENV_PATH, "w") as f:
            f.write("# Environment Configuration\n")
    set_key(ENV_PATH, "X_AUTH_TOKEN", auth_token)
    set_key(ENV_PATH, "X_CT0", ct0)

def extract_and_save_tokens():
    """Extrait les cookies de session X depuis les navigateurs installés."""
    loaders = [
        ("Chrome", browser_cookie3.chrome),
        ("Brave", browser_cookie3.brave),
        ("Arc / Chromium", browser_cookie3.chromium),
        ("Edge", browser_cookie3.edge),
        ("Firefox", browser_cookie3.firefox),
        ("Safari", browser_cookie3.safari),
    ]

    for name, loader in loaders:
        try:
            cj = loader(domain_name=".x.com")
            cookie_dict = {c.name: c.value for c in cj if c.domain in [".x.com", "x.com", ".twitter.com"]}
            auth_token = cookie_dict.get("auth_token")
            ct0 = cookie_dict.get("ct0")

            if auth_token and ct0:
                update_env(auth_token, ct0)
                return True, f"Session X synchronisée avec succès depuis {name}."
        except Exception:
            continue

    return False, "Aucune session active détectée. Connecte-toi à x.com sur ton navigateur."

if __name__ == "__main__":
    success, msg = extract_and_save_tokens()
    print(msg)
