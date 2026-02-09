import re
from datetime import datetime

class DataValidator:
    """Valide les données avant traitement."""
    
    @staticmethod
    def validate_article(article):
        """Vérifie qu'un article a tous les champs requis."""
        required_fields = ['title', 'description', 'publishedAt', 'url']
        if not all(field in article and article[field] for field in required_fields):
            return False, "Champs requis manquants ou vides."
        if not re.match(r'https?://.+', article['url']):
            return False, "URL invalide."
        try:
            datetime.fromisoformat(article['publishedAt'].replace('Z', ''))
        except (ValueError, TypeError):
            return False, "Format de date invalide."
        return True, "OK"
    
    @staticmethod
    def sanitize_query(query):
        """Nettoie et sécurise une requête utilisateur."""
        query = re.sub(r'[^\w\s\-éèêëàâäôöùûüïîç]', '', query) # Garde les caractères utiles
        query = query[:200] # Limite la longueur
        query = ' '.join(query.split()) # Enlève les espaces multiples
        return query.strip()