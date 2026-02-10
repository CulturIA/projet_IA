import re
import unicodedata
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from newspaper import Article, Config as NewspaperConfig
from config import config

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Synonymes pour l'expansion de requête
QUERY_EXPANSION = {
    "psg": ["paris saint-germain", "mbappé", "ligue 1", "football"],
    "om": ["olympique de marseille", "ligue 1", "football"],
    "ia": ["intelligence artificielle", "chatgpt", "openai", "tech"],
    "macron": ["emmanuel macron", "président", "elysée", "politique"],
    "usa": ["états-unis", "amérique", "biden", "trump"],
    "cinéma": ["film", "acteur", "hollywood", "série", "netflix"],
    "tech": ["technologie", "smartphone", "apple", "google", "startup"],
    "crypto": ["bitcoin", "ethereum", "blockchain", "finance"],
    "jo": ["jeux olympiques", "médaille", "sport", "athlète"]
}

def remove_accents(input_str):
    """Normalise une chaîne de caractères (supprime les accents)."""
    if not input_str: return ""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def get_search_query(question):
    """
    Transforme une question utilisateur en mots-clés optimisés.
    Exemple: "C'est quoi le score du PSG ?" -> keywords: ["score", "psg", "football"]
    """
    question_clean = remove_accents(question.lower().strip())
    words = re.findall(r'\w+', question_clean)
    
    meaningful_words = [word for word in words if word and word not in config.STOP_WORDS]
    
    if not meaningful_words:
        return {"principal": [question], "secondaire": [], "expanded": []}
    
    # Expansion de requête (Synonymes)
    expanded_terms = []
    for word in meaningful_words:
        if word in QUERY_EXPANSION:
            expanded_terms.extend(QUERY_EXPANSION[word])
            
    return {
        "principal": meaningful_words, 
        "secondaire": [], 
        "expanded": list(set(expanded_terms))
    }

def analyze_sentiment(text):
    """Analyse rudimentaire du sentiment (Positif/Négatif) par mots-clés."""
    if not text: return "😐 (Neutre)"
    
    MOTS_POS = {"victoire", "succès", "hausse", "accord", "gagne", "super", "meilleur", "joie", "avancée"}
    MOTS_NEG = {"défaite", "crise", "guerre", "mort", "chute", "échec", "problème", "grave", "danger"}
    
    text_clean = remove_accents(text.lower())
    words = re.findall(r'\w+', text_clean)
    
    score = sum(1 for w in words if w in MOTS_POS) - sum(1 for w in words if w in MOTS_NEG)
        
    if score > 0: return "😃 (Positif)"
    elif score < 0: return "😡 (Négatif)"
    return "😐 (Neutre)"

def calculate_score(article, keywords_dict):
    """
    Algorithme de pertinence : attribue un score à un article selon les mots-clés trouvés.
    """
    score = 0
    titre = remove_accents(article['titre'].lower())
    desc = remove_accents(article.get('description', '').lower())
    
    targets = keywords_dict.get("principal", []) + keywords_dict.get("expanded", [])
    
    for word in targets:
        w_clean = remove_accents(word.lower())
        # Le titre a plus de poids (x3) que la description
        if w_clean in titre: score += 30 
        if w_clean in desc: score += 10
    return score

def scrape_article_content(url):
    """Télécharge le contenu d'un article en simulant un navigateur (User-Agent)."""
    try:
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        conf = NewspaperConfig()
        conf.browser_user_agent = user_agent
        conf.request_timeout = config.API_TIMEOUT
        
        article = Article(url, config=conf, language='fr')
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        logger.warning(f"Échec scraping {url}: {e}")
        return None

def scrape_articles_parallel(articles, max_workers=5):
    """Exécute le scraping de plusieurs articles en parallèle (Multithreading)."""
    def scrape_single(article):
        content = scrape_article_content(article['url'])
        article['contenu_complet'] = content if content else article['description']
        return article
    
    scraped = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scrape_single, art): art for art in articles}
        for future in as_completed(futures):
            try:
                res = future.result()
                if res: scraped.append(res)
            except Exception: pass
    return scraped