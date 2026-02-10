import json
import os
import logging
from config import config

logger = logging.getLogger(__name__)

def _load_json(file_path):
    """Fonction utilitaire pour charger un JSON en toute sécurité."""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Erreur lecture {file_path}: {e}")
            return [] if "list" in str(type([])) else {} # Retour par défaut
    return []

def _save_json(data, file_path):
    """Fonction utilitaire pour sauvegarder un JSON."""
    try:
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        logger.error(f"Erreur écriture {file_path}: {e}")

def load_ratings():
    return _load_json(config.RATINGS_FILE) or {}

def save_ratings(ratings):
    _save_json(ratings, config.RATINGS_FILE)

def load_favorites():
    return _load_json(config.FAVORITES_FILE) or []

def save_favorites(favorites):
    _save_json(favorites, config.FAVORITES_FILE)