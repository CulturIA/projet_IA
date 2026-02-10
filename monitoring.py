import streamlit as st
import json
import logging
from datetime import datetime
from config import config
from persistence import save_favorites

logger = logging.getLogger(__name__)

class AppMonitoring:
    """Gère l'historique utilisateur, les statistiques et les favoris."""
    
    def __init__(self):
        self.load_stats()
    
    def load_stats(self):
        """Charge les stats globales (ou crée le fichier si absent)."""
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        if config.STATS_FILE.exists():
            try:
                with open(config.STATS_FILE, 'r') as f:
                    self.stats = json.load(f)
            except json.JSONDecodeError:
                self._reset_stats()
        else:
            self._reset_stats()

    def _reset_stats(self):
        self.stats = {"total_searches": 0, "total_articles_viewed": 0, "most_searched_terms": {}}
    
    def _save_stats(self):
        try:
            with open(config.STATS_FILE, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            logger.error(f"Erreur sauvegarde stats: {e}")
    
    def log_search(self, query):
        """Enregistre une nouvelle recherche dans les stats."""
        self.stats["total_searches"] = self.stats.get("total_searches", 0) + 1
        terms = self.stats.get("most_searched_terms", {})
        terms[query] = terms.get(query, 0) + 1
        self.stats["most_searched_terms"] = terms
        self._save_stats()
    
    def log_article_view(self, article):
        """Ajoute un article à l'historique de lecture."""
        self.stats["total_articles_viewed"] = self.stats.get("total_articles_viewed", 0) + 1
        self._save_stats()

        entry = {
            "titre": article['titre'],
            "url": article['url'],
            "date": article['date'],
            "timestamp": datetime.now().isoformat()
        }
        
        # Gestion doublons : on remonte l'article s'il existe déjà
        history = st.session_state.viewed_articles
        history = [h for h in history if h['url'] != article['url']]
        history.insert(0, entry)
        
        st.session_state.viewed_articles = history[:20] # On garde les 20 derniers
        self.save_history(st.session_state.viewed_articles, config.VIEWED_ARTICLES_FILE)

    def load_history(self, file_path):
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: return []
        return []

    def save_history(self, history_list, file_path):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(history_list, f, indent=4)
        except Exception as e:
            logger.error(f"Erreur sauvegarde historique: {e}")

    def toggle_favorite(self, article):
        """Ajoute ou retire un favori."""
        fav_urls = [fav['url'] for fav in st.session_state.favorites]
        
        if article['url'] in fav_urls:
            st.session_state.favorites = [f for f in st.session_state.favorites if f['url'] != article['url']]
            st.toast(f"💔 Retiré : {article['titre'][:20]}...", icon="🗑️")
        else:
            st.session_state.favorites.insert(0, article)
            st.toast(f"❤️ Ajouté : {article['titre'][:20]}...", icon="✅")
            
        save_favorites(st.session_state.favorites)