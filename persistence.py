import json
import os
from config import config

def load_ratings():
    # ... (Code existant inchangé) ...
    if os.path.exists(config.RATINGS_FILE):
        try:
            with open(config.RATINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_ratings(ratings):
    # ... (Code existant inchangé) ...
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.RATINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(ratings, f, indent=4)

# --- NOUVELLES FONCTIONS POUR LES FAVORIS ---
def load_favorites():
    fav_file = config.DATA_DIR / "favorites.json"
    if fav_file.exists():
        try:
            with open(fav_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return []
    return []

def save_favorites(favorites):
    fav_file = config.DATA_DIR / "favorites.json"
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(fav_file, 'w', encoding='utf-8') as f:
        json.dump(favorites, f, indent=4)