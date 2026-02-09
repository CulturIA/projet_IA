import streamlit as st
import json
from pathlib import Path
from datetime import datetime
from config import config

class AppMonitoring:
    """Monitoring basique de l'application et gestion des notes."""
    
    def __init__(self):
        self.stats_file = config.DATA_DIR / "stats.json"
        self.ratings_file = config.RATINGS_FILE
        self.search_history_file = config.DATA_DIR / "search_history.json"
        self.viewed_articles_file = config.DATA_DIR / "viewed_articles.json"
        self.load_stats()
    
    def load_stats(self):
        """Charge les statistiques d'usage."""
        self.stats_file.parent.mkdir(exist_ok=True)
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f: self.stats = json.load(f)
            except json.JSONDecodeError: self._reset_stats()
        else:
            self._reset_stats()

    # Renommé en méthode privée pour clarté
    def _reset_stats(self):
        self.stats = {"total_searches": 0, "total_articles_viewed": 0, "most_searched_terms": {}}
    
    # Renommé en méthode privée pour clarté
    def _save_stats(self):
        """Sauvegarde les statistiques."""
        with open(self.stats_file, 'w') as f: json.dump(self.stats, f, indent=2)
    
    def log_search(self, query):
        """Enregistre une recherche."""
        self.stats["total_searches"] = self.stats.get("total_searches", 0) + 1
        terms = self.stats.get("most_searched_terms", {})
        terms[query] = terms.get(query, 0) + 1
        self.stats["most_searched_terms"] = terms
        self._save_stats()
    
    def log_article_view(self, article):
        """Enregistre un article consulté dans l'historique."""
        self.stats["total_articles_viewed"] = self.stats.get("total_articles_viewed", 0) + 1
        self._save_stats()

        # Ajoute l'article à l'historique de session
        new_entry = {
            "titre": article['titre'],
            "url": article['url'],
            "timestamp": datetime.now().isoformat()
        }
        # Évite les doublons en tête de liste
        if new_entry['titre'] not in [a['titre'] for a in st.session_state.viewed_articles]:
            st.session_state.viewed_articles.insert(0, new_entry)
            # Limite l'historique aux 50 derniers articles
            st.session_state.viewed_articles = st.session_state.viewed_articles[:50]
            self.save_history(st.session_state.viewed_articles, self.viewed_articles_file)

    def log_full_search(self, query):
        """Enregistre la recherche complète de l'utilisateur."""
        if query not in st.session_state.search_history:
            st.session_state.search_history.insert(0, query)
            # Limite l'historique aux 50 dernières recherches
            st.session_state.search_history = st.session_state.search_history[:50]
            self.save_history(st.session_state.search_history, self.search_history_file)
    
    def load_ratings(self):
        """Charge les notes depuis ratings.json."""
        config.DATA_DIR.mkdir(exist_ok=True)
        if self.ratings_file.exists():
            try:
                with open(self.ratings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def save_ratings(self, ratings):
        """Sauvegarde les notes dans ratings.json."""
        with open(self.ratings_file, 'w', encoding='utf-8') as f:
            json.dump(ratings, f, indent=4)
    
    def load_history(self, file_path):
        """Charge un fichier d'historique (recherches ou articles)."""
        config.DATA_DIR.mkdir(exist_ok=True)
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def save_history(self, history_list, file_path):
        """Sauvegarde une liste d'historique dans un fichier."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(history_list, f, indent=4)

    def display_stats(self):
        """Affiche les statistiques dans la sidebar."""
        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 Statistiques d'Usage")
        st.sidebar.metric("Recherches totales", self.stats.get("total_searches", 0))
        st.sidebar.metric("Articles consultés", self.stats.get("total_articles_viewed", 0))