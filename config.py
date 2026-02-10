import os
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

class Config:
    """Configuration centralisée de l'application"""
    
    # Chemins
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "data"
    RATINGS_FILE = DATA_DIR / "ratings.json"
    
    # API Configuration
    @property
    def GNEWS_API_KEY(self):
        load_dotenv()
        api_key = os.getenv("GNEWS_API_KEY")
        if not api_key and "GNEWS_API_KEY" in st.secrets:
            api_key = st.secrets["GNEWS_API_KEY"]
        
        # Clé de secours (Change-la si elle ne marche plus !)
        if not api_key or api_key == "VOTRE_CLE_API_GNEWS_ICI":
            return "bcebac0ef1ab86a99f96b6f1238b98b6" 
        return api_key
    
    # Paramètres API & Scraping
    MAX_ARTICLES_TO_SCRAPE = 20
    CACHE_DURATION = 600
    DEFAULT_NUM_ARTICLES = 5
    MAX_NUM_ARTICLES = 20
    
    # --- LA LIGNE QUI MANQUAIT ---
    API_TIMEOUT = 10  # Temps max en secondes pour attendre une réponse
    # -----------------------------
    
    # Mots à ignorer (STOP_WORDS)
    STOP_WORDS = set([
        "le", "l", "la", "les", "un", "une", "des", "de", "du", "au", "aux", "et", "ou", "est", "sont", "a", "ont", "qui", "que", "quoi", "dont", "où", "je", "tu", "il", "elle", "nous", "vous", "ils", "elles", "quel", "quelle", "quelles", "quels", "mon", "ton", "son", "notre", "votre", "leur", "dans", "sur", "avec", "pour", "par", "sans", "comment", "pourquoi", "quand",
        "exemple", "est-ce", "ce", "ça", "fait", "faire", "une", "nouvelle", "nouveau", "en", "si", "plus", "moins", "très", "trop", "beaucoup", "vraiment", "va", "vas", "veut", "veux", "veulent", "sais", "sait", "savent", "connais", "connait", "connaissent", "y", "t", "s", "d"
    ])

# Instanciation pour export
config = Config()