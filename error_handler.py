import streamlit as st
import logging
from functools import wraps
import traceback
import requests
from newspaper import Article, ArticleException

from config import config

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class APIError(Exception): pass
class ScrapingError(Exception): pass

def handle_errors(func):
    """Décorateur pour gérer les erreurs de manière élégante."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except APIError as e:
            logger.error(f"Erreur API: {str(e)}")
            st.error(f"⚠️ Problème avec l'API: {str(e)}")
        except ScrapingError as e:
            logger.warning(f"Erreur scraping: {str(e)}")
            st.warning(f"📰 Impossible de récupérer l'article: {str(e)}")
        except Exception as e:
            logger.critical(f"Erreur inattendue dans {func.__name__}: {str(e)}\n{traceback.format_exc()}")
            st.error("❌ Une erreur inattendue est survenue. L'équipe technique a été notifiée.")
        return None
    return wrapper

@handle_errors
def get_news_safe(keywords_dict, max_articles=20):
    """Version sécurisée de get_news avec gestion d'erreurs."""
    if not keywords_dict or not keywords_dict.get("principal"):
        raise APIError("Mots-clés manquants")
    
    query = " AND ".join(f'"{word}"' for word in keywords_dict["principal"])
    
    params = {
        "q": query, "lang": "fr",
        "max": min(max_articles, config.MAX_ARTICLES_PER_REQUEST),
        "apikey": config.GNEWS_API_KEY
    }
    
    try:
        response = requests.get("https://gnews.io/api/v4/search", params=params, timeout=config.API_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        if "errors" in data: raise APIError(f"Erreur de l'API: {data['errors']}")
        return data.get("articles", [])
    except requests.exceptions.Timeout: raise APIError("L'API met trop de temps à répondre.")
    except requests.exceptions.HTTPError as e: raise APIError(f"Erreur HTTP {e.response.status_code}. Vérifiez votre clé API et vos crédits.")
    except requests.exceptions.RequestException as e: raise APIError(f"Erreur réseau: {str(e)}")

@handle_errors
def scrape_article_safe(url):
    """Version sécurisée du scraping."""
    try:
        article = Article(url, language='fr')
        article.download()
        article.parse()
        if not article.text or len(article.text) < 100:
            raise ScrapingError("Contenu trop court ou vide.")
        return article.text
    except ArticleException as e:
        logger.warning(f"Échec scraping (newspaper3k) {url}: {str(e)}")
        raise ScrapingError("Impossible de parser l'article.")
    except Exception as e:
        logger.warning(f"Échec scraping général {url}: {str(e)}")
        raise ScrapingError("Une erreur est survenue lors de la récupération.")