import streamlit as st
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Import des modules locaux ---
from config import config
from error_handler import get_news_safe, scrape_article_safe, logger
from data_validator import DataValidator
from monitoring import AppMonitoring

# --- CONFIGURATION ET INITIALISATION ---
st.set_page_config(
    page_title="Mon IA",
    page_icon="🤖",
    layout="centered"
)

# Initialise le monitoring
monitoring = AppMonitoring()

# Constantes
STOP_WORDS = set([
    "le", "l", "la", "les", "un", "une", "des", "de", "du", "au", "aux", "et", "ou", "est", "sont", "a", "ont", "qui", "que", "quoi", "dont", "où", "je", "tu", "il", "elle", "nous", "vous", "ils", "elles", "quel", "quelle", "quelles", "quels", "mon", "ton", "son", "notre", "votre", "leur", "dans", "sur", "avec", "pour", "par", "sans", "comment", "pourquoi", "quand",
    "exemple", "est-ce", "ce", "ça", "fait", "faire", "une", "nouvelle", "nouveau", "en", "si", "plus", "moins", "très", "trop", "beaucoup", "vraiment", "va", "vas", "veut", "veux", "veulent", "sais", "sait", "savent", "connais", "connait", "connaissent", "y", "t", "s", "d"
])

# Initialisation de l'état de session pour les notes
if 'article_ratings' not in st.session_state:
    st.session_state.article_ratings = monitoring.load_ratings()
# Initialisation des historiques
if 'search_history' not in st.session_state:
    st.session_state.search_history = monitoring.load_history(monitoring.search_history_file)
if 'viewed_articles' not in st.session_state:
    st.session_state.viewed_articles = monitoring.load_history(monitoring.viewed_articles_file)


# --- FONCTIONS PRINCIPALES ---

def scrape_article_content(url):
    """
    Utilise newspaper3k pour extraire le contenu complet d'un article.
    Cette fonction est maintenant remplacée par scrape_article_safe de error_handler.py
    """
    return scrape_article_safe(url)

def scrape_articles_parallel(articles, max_workers=5):
    """
    Scrape le contenu de plusieurs articles en parallèle en utilisant le gestionnaire d'erreurs.
    Ajoute le champ 'contenu_complet' à chaque article.
    """
    def scrape_single(article):
        content = scrape_article_content(article['url'])
        article['contenu_complet'] = content # Peut être None si le scraping échoue
        return article
    
    scraped_articles = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scrape_single, art): art for art in articles}
        for future in as_completed(futures):
            try:
                result = future.result()
                if result: scraped_articles.append(result)
            except Exception as e:
                logger.error(f"Erreur dans le pool de scraping: {e}")
                # Ne pas ajouter l'article si le future a échoué pour éviter les erreurs
                pass
    
    return scraped_articles

def get_search_query(question):
    """
    Nettoie la question de l'utilisateur pour ne garder que les mots-clés pertinents.
    Retourne un dictionnaire avec les mots-clés principaux et secondaires.
    """
    sanitized_question = DataValidator.sanitize_query(question)
    # Correction : Utiliser re.findall pour extraire les mots en préservant les accents.
    # \w+ inclut les lettres, chiffres et underscore, et est compatible Unicode en Python 3.
    words = re.findall(r'\w+', sanitized_question.lower())
    meaningful_words = [word for word in words if word not in STOP_WORDS]
    
    if not meaningful_words:
        return {"principal": [question], "secondaire": []}
    
    # Mots qui sont souvent secondaires/contextuels (pas essentiels pour la recherche)
    mots_secondaires = {"vues", "nombre", "combien", "dernier", "dernière", "nouveau", "nouvelle", 
                        "récent", "récente", "sorti", "sortie", "annonce", "annoncé", "fait"}
    
    # Sépare les mots principaux (noms propres, sujets) des mots secondaires (contexte)
    mots_principaux = []
    mots_contexte = []
    
    for word in meaningful_words:
        # Les noms propres (première lettre majuscule dans la question originale) sont toujours principaux
        if any(word.lower() == w.lower() and w[0].isupper() for w in question.split() if w):
            mots_principaux.append(word)
        elif word in mots_secondaires:
            mots_contexte.append(word)
        else:
            mots_principaux.append(word)
    
    # Si on a que des mots secondaires, on les considère comme principaux
    if not mots_principaux:
        mots_principaux = meaningful_words
        mots_contexte = []
    
    logger.info(f"Mots-clés principaux : {mots_principaux}, secondaires : {mots_contexte}")
    
    return {"principal": mots_principaux, "secondaire": mots_contexte}

@st.cache_data(ttl=config.CACHE_DURATION)
def get_news_cached(keywords_dict, max_articles=20):
    """Version mise en cache de la recherche d'articles."""
    articles_raw = get_news_safe(keywords_dict, max_articles)
    if not articles_raw: return []

    formatted_articles = []
    for art in articles_raw:
        is_valid, _ = DataValidator.validate_article(art)
        if is_valid:
            date_obj = datetime.fromisoformat(art["publishedAt"].replace('Z', ''))
            formatted_articles.append({
                "titre": art["title"],
                "description": art.get("description") or "Pas de description disponible.",
                "theme": keywords_dict.get("principal", ["inconnu"])[0], # Ajout du thème basé sur la recherche
                "date": date_obj.strftime("%Y-%m-%d %H:%M"),
                "url": art["url"],
                "contenu_complet": None,
                "image": art.get("image")
            })
    return formatted_articles

def afficher_resultats_recherche(articles, keywords_dict, num_to_show):
    """Affiche les résultats de la recherche."""
    fade_in_css = """
    <style>
    @keyframes fadeIn {
      0% { opacity: 0; transform: translateY(15px); }
      100% { opacity: 1; transform: translateY(0); }
    }
    .fade-in {
      animation: fadeIn 0.5s ease-out;
    }
    </style>
    """
    st.markdown(fade_in_css, unsafe_allow_html=True)
    
    if not articles:
        st.warning("🤔 Aucun article trouvé pour cette recherche.")
        return

    with st.container():
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)

        # Scraping du contenu complet des articles
        st.info("📰 Récupération du contenu complet des articles...")
        articles_with_content = scrape_articles_parallel(articles)
        
        query_words = keywords_dict["principal"] + keywords_dict["secondaire"]
        mots_principaux = keywords_dict["principal"]
        mots_secondaires = keywords_dict["secondaire"]
        
        scored_articles = []
        for article in articles_with_content:
            # Utilise le contenu complet pour le scoring
            contenu = (article["titre"] + " " + (article.get("contenu_complet") or article.get("description", ""))).lower()
            mots_contenu = re.split(r'\W+', contenu)
            
            # Vérifie que TOUS les mots-clés PRINCIPAUX sont présents (obligatoire)
            mots_principaux_trouves = sum(1 for mot in mots_principaux if mot in mots_contenu)
            
            # Si tous les mots-clés principaux ne sont pas présents, on ignore l'article
            if mots_principaux_trouves < len(mots_principaux):
                continue
            
            # Calcul du score basé sur la fréquence des mots-clés
            score = sum(mots_contenu.count(mot) for mot in query_words)
            
            # Bonus si les mots-clés apparaissent dans le titre (plus pertinent)
            titre_lower = article["titre"].lower()
            mots_titre = re.split(r'\W+', titre_lower)
            bonus_titre = sum(20 for mot in mots_principaux if mot in mots_titre)
            score += bonus_titre
            
            # Bonus pour les mots secondaires (bonus, pas obligatoire)
            mots_secondaires_trouves = sum(1 for mot in mots_secondaires if mot in mots_contenu)
            score += mots_secondaires_trouves * 5
            
            # Bonus supplémentaire si plusieurs mots-clés principaux sont présents
            if mots_principaux_trouves > 1:
                score += mots_principaux_trouves * 10
            
            scored_articles.append({"article": article, "score": score})
        
        scored_articles.sort(key=lambda x: x["score"], reverse=True)

        if not scored_articles:
            st.warning("🤔 Aucun article pertinent trouvé après filtrage.")
            return

        meilleur_article = scored_articles[0]
        score_text = f"(Pertinence : {meilleur_article['score']} mots-clés trouvés)"
        st.success(f"✅ **Meilleur résultat** {score_text}")        
        with st.container(border=True):
            st.subheader(f"[{meilleur_article['article']['titre']}]({meilleur_article['article']['url']})")
            if meilleur_article['article']['image']:
                st.image(meilleur_article['article']['image'], use_container_width=True, caption=f"Source: {meilleur_article['article']['url']}")
            st.caption(f"📅 Date : {meilleur_article['article']['date']}")
            
            # Affiche un extrait du contenu complet
            contenu = meilleur_article['article'].get('contenu_complet')
            if not contenu or len(contenu) < 100:
                st.warning("Le contenu complet n'a pas pu être récupéré.")
            elif len(contenu) > 500:
                st.write(contenu[:500] + "...")
                with st.expander("Lire le contenu complet"):
                    st.write(contenu)
                    # Log l'article comme consulté quand l'utilisateur clique pour lire
                    monitoring.log_article_view(meilleur_article['article'])
            else:
                st.write(contenu)
            
            # Ajout de l'expander pour afficher les détails de la pertinence
            with st.expander("Détails de la pertinence"):
                word_counts = {}
                contenu_lower = (meilleur_article['article']['titre'] + " " + (meilleur_article['article'].get('contenu_complet') or meilleur_article['article'].get("description") or "")).lower()
                mots_contenu = re.split(r'\W+', contenu_lower)
                for mot in query_words:
                    count = mots_contenu.count(mot)
                    if count > 0:
                        word_counts[mot] = count
                
                if word_counts:
                    for mot, count in word_counts.items():
                        st.write(f"- **{mot}**: {count} fois")

        if len(scored_articles) > 1:
            st.write("---")
            st.info("🔎 **Autres résultats similaires :**")
            for res in scored_articles[1:num_to_show + 1]:
                score_text = f"| Pertinence : {res['score']}"
                expander_label = f"**{res['article']['titre']}** (📅 {res['article']['date']}) {score_text}"
                with st.expander(expander_label):
                    if res['article']['image']:
                        st.image(res['article']['image'], width=200)
                    contenu = res['article']['contenu_complet']
                    if contenu and len(contenu) > 300:
                        st.write(contenu[:300] + "...")
                        if st.button("Voir plus", key=f"voir_plus_{res['article']['titre']}"):
                            st.write(contenu)
                            # Log l'article comme consulté
                            monitoring.log_article_view(res['article'])
                    else:
                        st.write(contenu)
                    st.markdown(f"[🔗 Lire l'article complet sur le site]({res['article']['url']})")

        st.markdown('</div>', unsafe_allow_html=True)

def page_recherche(num_articles_to_show):
    """Contenu de la page de recherche par mots-clés."""
    st.header("🔍 Recherche par mots-clés")
    question = st.text_input("Posez votre question ou entrez des mots-clés ici :", key="search_query")

    if question:
        keywords_dict = get_search_query(question)
        mots_affiches = " + ".join(keywords_dict["principal"])
        if keywords_dict["secondaire"]:
            mots_affiches += f" (contexte: {', '.join(keywords_dict['secondaire'])})"
        st.write(f"Recherche d'articles pour : **{mots_affiches}**")
        
        with st.spinner(f"🔍 Recherche des actualités..."):
            articles = get_news_cached(keywords_dict, max_articles=config.MAX_ARTICLES_TO_SCRAPE)
        
        if articles:
            afficher_resultats_recherche(articles, keywords_dict, num_articles_to_show)
            monitoring.log_search(question)
            monitoring.log_full_search(question)

def page_generale(num_articles_to_show):
    """Contenu de la page générale pour parcourir les articles."""
    st.header("📰 Parcourir les articles")

    st.sidebar.subheader("Options d'affichage")
    theme_filter = st.sidebar.radio("Filtrer par thème", ["Sport", "Musique", "Jeux Vidéo", "Technologie", "Actualité"])
    sort_by = st.sidebar.radio("Trier par", ["Date (plus récent)", "Meilleures notes"])

    query = theme_filter if theme_filter != "Actualité" else "actualité générale"
    
    with st.spinner(f"Chargement des articles sur le thème '{query}'..."):
        articles_a_afficher = get_news_cached({"principal": [query], "secondaire": []}, max_articles=num_articles_to_show * 2)

    if sort_by == "Date (plus récent)":
        articles_a_afficher.sort(key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d %H:%M'), reverse=True)
    elif sort_by == "Meilleures notes":
        articles_a_afficher.sort(key=lambda x: st.session_state.article_ratings.get(x['titre'], 0), reverse=True)

    if not articles_a_afficher:
        st.warning("Aucun article à afficher pour cette catégorie.")
    else:
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)
        for i, article in enumerate(articles_a_afficher[:num_articles_to_show]):
            with st.container(border=True):
                st.subheader(f"[{article['titre']}]({article['url']})")
                if article['image']:
                    st.image(article['image'], use_container_width=True)
                st.caption(f"🎯 Thème : {article.get('theme', 'N/A').capitalize()} | 📅 Date : {article['date']}")
                st.write(article['description'])
                
                note_actuelle = st.session_state.article_ratings.get(article['titre'], 0)
                note = st.radio(
                    "Votre note :", 
                    options=[1, 2, 3, 4, 5], 
                    index=note_actuelle - 1 if note_actuelle > 0 else 2,
                    key=f"note_{article['titre']}_{i}", 
                    horizontal=True
                )
                
                if note_actuelle != note:
                    st.session_state.article_ratings[article['titre']] = note
                    monitoring.save_ratings(st.session_state.article_ratings)
                    st.rerun()
                
                note_display = st.session_state.article_ratings.get(article['titre'], 0)
                if note_display > 0:
                    st.markdown(f"**Votre note : {'⭐' * note_display}**")
                else:
                    st.markdown("_Pas encore noté_")
            st.write("")
        st.markdown('</div>', unsafe_allow_html=True)

# --- Logique principale de l'application ---

st.title("🤖 MON ASSISTANT IA")
st.write("**Spécialiste : Sport 🏆 • Musique 🎵 • Jeux Vidéo 🎮 • Actualité 🌍**")

st.sidebar.title("Navigation")
page = st.sidebar.radio("Choisissez une page", ["Recherche par mots-clés", "Parcourir les articles"])
st.sidebar.divider()

st.sidebar.subheader("Paramètres d'affichage")
num_articles = st.sidebar.number_input("Nombre d'articles à afficher", min_value=1, max_value=config.MAX_NUM_ARTICLES, value=config.DEFAULT_NUM_ARTICLES, step=1)
st.sidebar.divider()

# Affichage des stats de monitoring
monitoring.display_stats()

# Affichage des historiques dans la sidebar
st.sidebar.divider()
st.sidebar.subheader("Historiques")

with st.sidebar.expander("Recherches récentes"):
    if not st.session_state.search_history:
        st.write("_Aucune recherche pour l'instant._")
    else:
        for search in st.session_state.search_history:
            if st.button(search, key=f"hist_{search}", use_container_width=True):
                st.session_state.search_query = search
                st.rerun()

with st.sidebar.expander("Articles consultés"):
    if not st.session_state.viewed_articles:
        st.write("_Aucun article consulté._")
    else:
        for article in st.session_state.viewed_articles:
            st.markdown(f"- [{article['titre']}]({article['url']})")

if page == "Recherche par mots-clés":
    page_recherche(num_articles)
elif page == "Parcourir les articles":
    page_generale(num_articles)