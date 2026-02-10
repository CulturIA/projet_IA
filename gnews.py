import requests
import logging
from config import config

logger = logging.getLogger(__name__)

def get_news(keywords_dict, max_articles=20):
    """
    Interroge l'API GNews.io avec les mots-clés fournis.
    """
    api_key = config.GNEWS_API_KEY
    
    if not keywords_dict or not keywords_dict.get("principal"):
        logger.warning("Aucun mot-clé fourni pour la recherche.")
        return []
    
    query = " ".join(keywords_dict["principal"])
    
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
        articles = data.get("articles", [])
        logger.info(f"{len(articles)} articles trouvés via API pour : {query}")
        return articles
        
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"Erreur HTTP GNews: {http_err} - Vérifiez votre clé API ou vos quotas.")
        return []
    except Exception as e:
        logger.error(f"Erreur connexion GNews : {e}")
        return []