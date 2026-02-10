import logging
from gnews import get_news
from utils import scrape_article_content

logger = logging.getLogger(__name__)

def get_news_safe(keywords_dict, max_articles=20):
    """Wrapper sécurisé pour récupérer les news sans planter l'app."""
    try:
        return get_news(keywords_dict, max_articles)
    except Exception as e:
        logger.critical(f"Erreur critique GNews: {e}")
        return []

def scrape_article_safe(url):
    """Wrapper sécurisé pour le scraping."""
    try:
        return scrape_article_content(url)
    except Exception as e:
        logger.error(f"Erreur scraping {url} : {e}")
        return None