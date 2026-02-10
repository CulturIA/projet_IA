import logging
from gnews import get_news
from utils import scrape_article_content

# Configuration du logger pour le prof
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_news_safe(keywords_dict, max_articles=20):
    try:
        articles = get_news(keywords_dict, max_articles)
        return articles
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des news : {e}")
        return []

def scrape_article_safe(url):
    try:
        return scrape_article_content(url)
    except Exception as e:
        logger.error(f"Erreur lors du scraping de {url} : {e}")
        return None