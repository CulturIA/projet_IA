import streamlit as st
import json
from pathlib import Path
from datetime import datetime
from config import config
from persistence import save_favorites

class AppMonitoring:
    def __init__(self):
        self.stats_file = config.DATA_DIR / "stats.json"
        self.viewed_articles_file = config.DATA_DIR / "viewed_articles.json"
        self.load_stats()
    
    def load_stats(self):
        self.stats_file.parent.mkdir(parents=True, exist_ok=True)
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f: self.stats = json.load(f)
            except json.JSONDecodeError: self._reset_stats()
        else:
            self._reset_stats()

    def _reset_stats(self):
        self.stats = {"total_searches": 0, "total_articles_viewed": 0, "most_searched_terms": {}}
    
    def _save_stats(self):
        with open(self.stats_file, 'w') as f: json.dump(self.stats, f, indent=2)
    
    def log_search(self, query):
        self.stats["total_searches"] = self.stats.get("total_searches", 0) + 1
        terms = self.stats.get("most_searched_terms", {})
        terms[query] = terms.get(query, 0) + 1
        self.stats["most_searched_terms"] = terms
        self._save_stats()
    
    def log_article_view(self, article):
        """Enregistre un article comme 'Lu' dans l'historique."""
        # Stats globales
        self.stats["total_articles_viewed"] = self.stats.get("total_articles_viewed", 0) + 1
        self._save_stats()

        # Gestion de l'historique utilisateur (Liste d'articles)
        entry = {
            "titre": article['titre'],
            "url": article['url'],
            "date": article['date'],
            "timestamp": datetime.now().isoformat()
        }
        
        # On évite les doublons (si déjà vu, on le remonte en haut de la liste)
        history = st.session_state.viewed_articles
        history = [h for h in history if h['url'] != article['url']]
        history.insert(0, entry)
        
        # Limite à 20 articles
        st.session_state.viewed_articles = history[:20]
        self.save_history(st.session_state.viewed_articles, self.viewed_articles_file)

    def load_history(self, file_path):
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: return []
        return []

    def save_history(self, history_list, file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(history_list, f, indent=4)

    def toggle_favorite(self, article):
        """Ajoute/Retire des favoris sans recharger toute l'app via session_state."""
        fav_urls = [fav['url'] for fav in st.session_state.favorites]
        
        if article['url'] in fav_urls:
            st.session_state.favorites = [f for f in st.session_state.favorites if f['url'] != article['url']]
            # Petit toast discret
            st.toast(f"💔 Retiré : {article['titre'][:20]}...", icon="🗑️")
        else:
            st.session_state.favorites.insert(0, article)
            st.toast(f"❤︎ Ajouté : {article['titre'][:20]}...", icon="✅")
            
        save_favorites(st.session_state.favorites)