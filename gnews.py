import requests
from datetime import datetime
from config import config

def get_news(keywords_dict, max_articles=20):
    # Récupération de la clé API via l'objet config
    api_key = config.GNEWS_API_KEY
    
    if not keywords_dict or not keywords_dict.get("principal"):
        return []
    
    mots_principaux = keywords_dict["principal"]
    # On simplifie la requête pour l'API
    query = " ".join(mots_principaux)
    
    try:
        url = "https://gnews.io/api/v4/search"
        params = {
            "q": query, 
            "lang": "fr", 
            "max": max_articles, 
            "apikey": api_key
        }
        response = requests.get(url, params=params, timeout=config.API_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        return data.get("articles", [])
    except Exception as e:
        print(f"Erreur API GNews : {e}")
        return []