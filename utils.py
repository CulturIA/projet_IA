import re
import unicodedata
from newspaper import Article
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import config

# --- Dictionnaire d'expansion (Synonymes & Contexte) ---
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
    """Enlève les accents pour faciliter la comparaison (été -> ete)."""
    if not input_str: return ""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def scrape_article_content(url):
    """Utilise newspaper3k pour extraire le contenu."""
    try:
        article = Article(url, language='fr')
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        # print(f"Erreur scraping {url}: {e}") # On masque les erreurs dans la console
        return None

def scrape_articles_parallel(articles, max_workers=5):
    """Scrape en parallèle."""
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

def get_search_query(question):
    """
    Nettoie la question et ajoute des synonymes (Expansion de requête).
    """
    question_clean = remove_accents(question.lower().strip())
    words = re.findall(r'\w+', question_clean)
    
    meaningful_words = [word for word in words if word and word not in config.STOP_WORDS]
    
    if not meaningful_words:
        return {"principal": [question], "secondaire": [], "expanded": []}
    
    # Expansion de requête (Ajout de synonymes)
    expanded_terms = []
    for word in meaningful_words:
        if word in QUERY_EXPANSION:
            expanded_terms.extend(QUERY_EXPANSION[word])
    
    # On dédoublonne
    expanded_terms = list(set(expanded_terms))
    
    return {
        "principal": meaningful_words, 
        "secondaire": [], 
        "expanded": expanded_terms # Nouveaux mots clés cachés
    }

def analyze_sentiment(text):
    """Analyse basique (Positive/Négative) basée sur des listes de mots."""
    if not text: return "😐 (Neutre)"
    
    # Listes simplifiées pour l'exemple
    MOTS_POS = ["victoire", "succès", "hausse", "accord", "gagne", "super", "meilleur", "joie", "avancée"]
    MOTS_NEG = ["défaite", "crise", "guerre", "mort", "chute", "échec", "problème", "grave", "danger"]
    
    text_clean = remove_accents(text.lower())
    words = re.findall(r'\w+', text_clean)
    
    score = 0
    for w in words:
        if w in MOTS_POS: score += 1
        if w in MOTS_NEG: score -= 1
        
    if score > 0: return "😃 (Positif)"
    elif score < 0: return "😡 (Négatif)"
    else: return "😐 (Neutre)"