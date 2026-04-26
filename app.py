import streamlit as st
from datetime import datetime

# --- Imports des modules (MVC Pattern) ---
from config import config
from error_handler import get_news_safe
from monitoring import AppMonitoring
from persistence import load_favorites
from utils import (
    get_search_query, 
    analyze_sentiment, 
    calculate_score, 
    scrape_articles_parallel
)

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Culturia", page_icon="📰", layout="wide")

# --- 2. GESTION DE L'ÉTAT (SESSION STATE) ---
# Initialisation des variables globales de l'interface
if 'theme' not in st.session_state: st.session_state.theme = 'light'
if 'page' not in st.session_state: st.session_state.page = "Recherche"
if 'num_articles' not in st.session_state: st.session_state.num_articles = 10
if 'current_query' not in st.session_state: st.session_state.current_query = ""
if 'cached_results' not in st.session_state: st.session_state.cached_results = None
if 'opened_article_url' not in st.session_state: st.session_state.opened_article_url = None

# --- 3. FONCTIONS UI (THEME & CSS) ---
def toggle_theme():
    """Basculer entre Mode Clair et Sombre."""
    st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'

def inject_theme():
    """Injecte les variables CSS dynamiques selon le thème choisi."""
    if st.session_state.theme == 'dark':
        css = """
        :root { --bg-app: #363636; --text-main: #ffffff; --text-light: #b0b0b0; --accent: #60A5FA; --border: #444444; }
        """
    else:
        css = """
        :root { --bg-app: #ffffff; --text-main: #000000; --text-light: #000000; --accent: #2563EB; --border: #cccccc; }
        """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

def local_css(file_name):
    """Charge le fichier CSS externe."""
    try:
        with open(file_name, "r", encoding="utf-8") as f: st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError: pass

local_css("style.css")
inject_theme()

# --- 4. CHARGEMENT DONNÉES UTILISATEUR ---
monitoring = AppMonitoring()
if 'viewed_articles' not in st.session_state: 
    st.session_state.viewed_articles = monitoring.load_history(config.VIEWED_ARTICLES_FILE)
if 'favorites' not in st.session_state: 
    st.session_state.favorites = load_favorites()

# --- 5. LOGIQUE CONTROLEUR ---
def perform_search(query, num_articles):
    """
    Orchestre la recherche : 
    1. Nettoyage requête
    2. Appel API GNews (via cache)
    3. Scraping parallèle du contenu
    4. Calcul de pertinence
    5. Mise en cache des résultats
    """
    kw = get_search_query(query)
    # Récupération API (rapide)
    articles_raw = get_news_safe(kw, num_articles)
    
    if articles_raw:
        with st.spinner(f"Analyse approfondie de {len(articles_raw)} articles sur '{query}'..."):
            # Formatage initial
            articles_formatted = []
            for art in articles_raw:
                try:
                    d = art.get("publishedAt", "")
                    date_str = datetime.fromisoformat(d.replace('Z', '')).strftime("%d %b. %Y").upper()
                    articles_formatted.append({
                        "titre": art.get("title", "Sans titre"),
                        "description": art.get("description", ""),
                        "titre": art.get("title") or "Sans titre",
                        "description": art.get("description") or "",
                        "date": date_str,
                        "url": art.get("url", "#"),
                        "image": art.get("image"),
                        "contenu_complet": None,
                        "theme": kw.get("principal", ["Général"])[0].upper()
                    })
                except Exception: continue

            # Scraping (lent, donc parallèle)
            articles_full = scrape_articles_parallel(articles_formatted)
            # Tri par pertinence
            articles_full.sort(key=lambda x: calculate_score(x, kw), reverse=True)
            
            st.session_state.cached_results = articles_full
    else:
        st.session_state.cached_results = []
    
    st.session_state.current_query = query

def is_favorite(article):
    """Vérifie si l'article est déjà en favori."""
    return any(f['url'] == article['url'] for f in st.session_state.favorites)

# --- 6. COMPOSANTS D'AFFICHAGE ---
def generer_html_card_content(art, is_hero=False):
    """Génère le HTML pour une carte (Hero ou Grid)."""
    sentiment = analyze_sentiment(art.get('description', ''))
    img_html = f'<div class="{ "hero" if is_hero else "grid" }-image-box"><img src="{art["image"]}"></div>' if art.get('image') else ""
    
    if is_hero:
        return f"""
        <div class="hero-container">
            {img_html}
            <div>
                <span class="hero-meta">À LA UNE • {art['theme']}</span>
                <h1 class="hero-title">{art['titre']}</h1>
                <div class="hero-desc">{art['description']}</div>
                <div class="card-footer" style="border:none; margin-top:10px;"><span>{art['date']}</span><span>Tonalité : {sentiment}</span></div>
            </div>
        </div>
        """
    else:
        return f"""
        <div class="grid-card">
            <span class="hero-meta" style="font-size:0.65rem;">{art['theme']}</span>
            {img_html}
            <h3 class="grid-title">{art['titre']}</h3>
            <div class="grid-desc">{art['description'][:100]}...</div>
            <div class="card-footer"><span>{art['date']}</span><span>{sentiment}</span></div>
        </div>
        """

def afficher_article_interactif(article, is_hero=False, index=0):
    """Affiche une carte complète avec ses boutons interactifs."""
    st.markdown(generer_html_card_content(article, is_hero), unsafe_allow_html=True)
    c1, c2 = st.columns([1, 4])
    
    # Bouton Favoris
    fav_label = "💔 Retirer" if is_favorite(article) else "❤️ Favoris"
    if c1.button(fav_label, key=f"fav_{index}_{article['url']}"):
        monitoring.toggle_favorite(article)
        st.rerun() 
        
    # Bouton Lire
    is_open = (st.session_state.opened_article_url == article['url'])
    btn_label = "📖 Fermer" if is_open else "📖 Lire l'article"
    
    if c2.button(btn_label, key=f"read_{index}_{article['url']}"):
        if is_open: st.session_state.opened_article_url = None
        else:
            st.session_state.opened_article_url = article['url']
            monitoring.log_article_view(article)
        st.rerun()

    # Zone Lecture Dépliée
    if is_open:
        st.info(f"Source : {article['url']}")
        st.markdown(f"""
        <div style="background:var(--bg-app); border:1px solid var(--accent); padding:20px; margin-bottom:20px;">
            <h3 style="margin-top:0;">Contenu complet</h3>
            <p style="line-height:1.6; font-family:'Lora',serif;">{article.get('contenu_complet', 'Contenu non disponible')}</p>
            <p style="line-height:1.6; font-family:'Lora',serif;">{article.get('contenu_complet') or 'Contenu non disponible'}</p>
            <a href="{article['url']}" target="_blank" style="display:block; margin-top:10px; color:var(--accent); font-weight:bold;">🔗 Lire sur le site d'origine</a>
        </div>
        """, unsafe_allow_html=True)

# --- 7. HEADER & NAVIGATION ---
with st.container():
    st.markdown('<div class="nav-wrapper">', unsafe_allow_html=True)
    c1, c2, c3, c4, c5, c6 = st.columns([1, 1, 1, 1, 1, 0.5])
    
    with c1: 
        if st.button("🔍 RECHERCHE", key="nav_search", use_container_width=True): 
            st.session_state.page = "Recherche"; st.rerun()
    with c2: 
        if st.button("📂 RUBRIQUES", key="nav_browse", use_container_width=True): 
            st.session_state.page = "Parcourir"; st.rerun()
    with c3: 
        if st.button("❤️ FAVORIS", key="nav_fav", use_container_width=True): 
            st.session_state.page = "Favoris"; st.rerun()
    with c4:
        with st.expander("HISTORIQUE"):
             if st.session_state.viewed_articles:
                 for art in st.session_state.viewed_articles:
                     if st.button(f"📄 {art['titre'][:25]}...", key=f"hist_btn_{art['url']}"):
                         st.session_state.opened_article_url = art['url']
                         st.markdown(f"[Ouvrir]({art['url']})")
             else: st.write("Vide")
    with c5:
        sc = st.columns([1, 2, 1]) 
        if sc[0].button("−", key="btn_minus", use_container_width=True):
            st.session_state.num_articles = max(1, st.session_state.num_articles-1); st.rerun()
        sc[1].markdown(f"<div class='counter-box'>{st.session_state.num_articles} ACTUS</div>", unsafe_allow_html=True)
        if sc[2].button("✚", key="btn_plus", use_container_width=True):
            st.session_state.num_articles = min(40, st.session_state.num_articles+1); st.rerun()
    with c6:
        icon = "🌙" if st.session_state.theme == 'light' else "☀️"
        if st.button(icon, key="btn_theme"): toggle_theme(); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 8. CORPS DE PAGE ---
st.markdown(f"""
    <div class="brand-title" translate="no" class="notranslate">Culturia</div>
    <div style="text-align: center; padding-top: 20px; font-family: 'Lora', serif; color: var(--text-light); font-style: italic; margin-top: -15px; margin-bottom: 30px;">Created by Noam Boutounas & Maxime Navellier</div>
    <div class="tagline-container"><div class="tagline-line"></div><div class="tagline">{datetime.now().strftime('%A %d %B %Y').capitalize()} — L'information augmentée</div></div>
""", unsafe_allow_html=True)

# --- ROUTAGE (PAGES) ---
if st.session_state.page == "Recherche":
    query = st.text_input("Recherche", value=st.session_state.current_query, placeholder="Sujet, personnalité...", label_visibility="collapsed")
    
    if query and query != st.session_state.current_query:
        monitoring.log_search(query)
        perform_search(query, st.session_state.num_articles)
        st.rerun()

    if st.session_state.cached_results:
        st.markdown(f"<div style='text-align:center; font-style:italic; margin-bottom:40px; color:var(--text-light);'>Résultats pour : {st.session_state.current_query}</div>", unsafe_allow_html=True)
        results = st.session_state.cached_results
        
        if results: afficher_article_interactif(results[0], is_hero=True, index=0)
        if len(results) > 1:
            cols = st.columns(2, gap="large") 
            for i, art in enumerate(results[1:]):
                with cols[i % 2]: afficher_article_interactif(art, is_hero=False, index=i+1)
    
    elif st.session_state.current_query:
        st.warning("Aucun résultat trouvé pour cette recherche.")

elif st.session_state.page == "Favoris":
    st.markdown("<h2 style='text-align:center; font-family:serif; margin:30px 0;'>— VOS ARTICLES FAVORIS —</h2>", unsafe_allow_html=True)
    if not st.session_state.favorites:
        st.info("Votre liste est vide.")
    else:
        favs = st.session_state.favorites[::-1]
        if favs: afficher_article_interactif(favs[0], is_hero=True, index=999)
        if len(favs) > 1:
            cols = st.columns(2, gap="large") 
            for i, art in enumerate(favs[1:]):
                with cols[i % 2]: afficher_article_interactif(art, is_hero=False, index=1000+i)

elif st.session_state.page == "Parcourir":
    st.write("")
    cats = ["Politique", "Monde", "Économie", "Tech", "Sciences", "Santé", 
            "Sport", "Culture", "Cinéma", "Musique", "Gaming", "Environnement"]
    
    rows = [cats[:6], cats[6:]]
    
    for row_cats in rows:
        cols = st.columns(6)
        for i, cat in enumerate(row_cats):
            is_active = (st.session_state.current_query == cat)
            if cols[i].button(cat, key=f"cat_{cat}", disabled=is_active, use_container_width=True):
                perform_search(cat, st.session_state.num_articles)
                st.rerun()
                
    st.markdown("---")
    
    if st.session_state.current_query in cats and st.session_state.cached_results:
        st.markdown(f"<h2 style='text-align:center; font-family:serif; letter-spacing:2px; margin:30px 0;'>— {st.session_state.current_query.upper()} —</h2>", unsafe_allow_html=True)
        results = st.session_state.cached_results
        
        if results: afficher_article_interactif(results[0], is_hero=True, index=2000)
        if len(results) > 1:
            cols = st.columns(2, gap="large") 
            for i, art in enumerate(results[1:]):
                with cols[i % 2]: afficher_article_interactif(art, is_hero=False, index=2001+i)
