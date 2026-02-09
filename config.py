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
        """Récupère la clé API depuis les variables d'environnement ou secrets Streamlit"""
        load_dotenv() # Charge le fichier .env
        
        # Essaye d'abord de lire le .env local, ce qui fonctionnera toujours sur votre machine
        api_key = os.getenv("GNEWS_API_KEY")
        
        # Si la clé n'est pas dans .env, alors on vérifie les secrets Streamlit (pour le déploiement)
        if not api_key and "GNEWS_API_KEY" in st.secrets:
            api_key = st.secrets["GNEWS_API_KEY"]

        if not api_key or api_key == "VOTRE_CLE_API_GNEWS_ICI":
            st.error("⚠️ Clé API GNews manquante ou non configurée ! Ajoutez GNEWS_API_KEY dans un fichier .env ou dans les secrets Streamlit.")
            st.stop()
        return api_key
    
    # Limites API
    MAX_ARTICLES_PER_REQUEST = 100
    MAX_ARTICLES_TO_SCRAPE = 20
    API_TIMEOUT = 10  # secondes
    
    # Cache
    CACHE_DURATION = 600  # 10 minutes en secondes
    
    # Interface
    DEFAULT_NUM_ARTICLES = 5
    MAX_NUM_ARTICLES = 20
    
    # Scraping
    SCRAPING_TIMEOUT = 10

# Instanciation
config = Config()