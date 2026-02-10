import os
from pathlib import Path
import streamlit as st

# On tente d'importer dotenv, mais on ne plante pas si ça manque
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class Config:
    """
    Classe de configuration centralisée (Pattern Singleton).
    Regroupe toutes les constantes et chemins du projet.
    """
    
    # --- CHEMINS ---
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "data"
    RATINGS_FILE = DATA_DIR / "ratings.json"
    STATS_FILE = DATA_DIR / "stats.json"
    VIEWED_ARTICLES_FILE = DATA_DIR / "viewed_articles.json"
    FAVORITES_FILE = DATA_DIR / "favorites.json"
    
    # --- PARAMÈTRES API ---
    @property
    def GNEWS_API_KEY(self):
        """Récupère la clé API avec ordre de priorité : .env > st.secrets > Hardcodé."""
        # 1. Variable d'environnement (.env)
        api_key = os.getenv("GNEWS_API_KEY")
        if api_key: return api_key
        
        # 2. Streamlit Cloud Secrets
        if "GNEWS_API_KEY" in st.secrets:
            return st.secrets["GNEWS_API_KEY"]
            
        # 3. Fallback (Clé de secours)
        return "bcebac0ef1ab86a99f96b6f1238b98b6"

    MAX_ARTICLES_TO_SCRAPE = 20
    CACHE_DURATION = 3600  # 1 heure
    API_TIMEOUT = 10      # Secondes avant abandon

    # --- NLP (Traitement Langage) ---
    STOP_WORDS = {
        "le", "la", "les", "un", "une", "des", "de", "du", "au", "aux", "et", "ou", 
        "est", "sont", "a", "ont", "qui", "que", "quoi", "dont", "où", "je", "tu", 
        "il", "elle", "nous", "vous", "ils", "elles", "dans", "sur", "avec", "pour", 
        "par", "sans", "comment", "pourquoi", "quand", "ce", "cette", "cet", "ces",
        "en", "si", "plus", "moins", "très", "trop", "mais", "donc", "or", "ni", "car"
    }

config = Config()