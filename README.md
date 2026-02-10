# 🏛️ Culturia
### *L'Assistant Culturel Intelligent & Immersif*

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Status](https://img.shields.io/badge/Status-En_Développement-green?style=for-the-badge)

> **Culturia** réinvente la veille culturelle. Fini le scroll infini : accédez à une agrégation intelligente d'articles sur le **Sport**, la **Musique**, les **Jeux Vidéo** et l'**Actualité**, présentée dans une interface simple d'utilisation et accessible a tous.

---

## 📸 Aperçu

| Page d'Accueil | Lecture d'Article |
|:---:|:---:|
| *Interface de recherche épurée* | *Mode lecture immersive* |
| <img width="1902" height="625" alt="image" src="https://github.com/user-attachments/assets/673db9ad-bb5e-4455-b3e3-9518d55d70a1" />|<img width="890" height="947" alt="image" src="https://github.com/user-attachments/assets/70f0ca82-a4ab-4559-85fb-b977d6cb9a29" />


---

## ✨ Fonctionnalités Clés

### 🎨 1. Expérience Utilisateur "Néo-Journal"
Nous avons cassé les codes de Streamlit pour offrir une **expérience visuelle unique** :
* **Design Sur-Mesure :** Injection de CSS avancé pour une interface élégante (Police *Playfair Display* & *Merriweather*).
* **Hero Cards & Grilles :** Une mise en page hiérarchisée avec un article "à la une" et une grille secondaire structurée.
* **Harmonie Visuelle :** Toutes les images sont automatiquement redimensionnées et recadrées au format **16/9** pour un rendu impeccable.
* **Barre de Contrôle Unifiée :** Navigation fluide entre la *Recherche*, le mode *Parcourir*, l'*Historique* et les *Paramètres*.

### 🧠 2. Moteur de Recherche Intelligent
* **Analyse Sémantique :** L'algorithme distingue le **sujet principal** des termes contextuels pour affiner les résultats.
* **Correction Orthographique  :** Module de détection automatique des fautes de frappe (ex: *"Mbape"* → *"Mbappe"*).
* **Scoring de Pertinence :** Calcul dynamique du score de chaque article basé sur la fréquence et la position des mots-clés (si le mot est présent dans le titre, la description...).
* **Transparence :** Chaque résultat affiche une section **"Mots en commun"** détaillant les correspondances trouvées.

### 📖 3. Lecture Optimisée
* **Contenu Intégré :** Plus besoin de quitter l'application. Lisez l'intégralité de l'article via le bouton dépliant **"Lire la suite"**.
* **Historique de Session 🕒 :** Retrouvez instantanément vos 10 dernières lectures via un menu déroulant dédié.
* **Filtrage Thématique :** Explorez les articles par catégories (*Sport, Tech, Musique...*) en un clic.

---

## 🛠️ Stack Technique

* **Framework :** `Streamlit` (Frontend & Backend léger)
* **Data & API :** `GNews` (Flux temps réel), `Newspaper3k` (Scraping de contenu)
* **Traitement :** `Python` (Multi-threading, Regex, Logique de scoring)
* **Persistance :** `JSON` (Sauvegarde locale des notes et préférences >*EN DEVELOPPEMENT*)

---

## 🚀 Installation & Démarrage

Suivez ces étapes pour lancer **Culturia** sur votre machine locale :
1. Telecharger tout les fichiers présent sur le Github.
   
2. Installer les dépendances

```Bash
pip install -r requirements.txt
```
3. Lancer l'application
```Bash

streamlit run app.py
```
👥 Equipe développement
Projet réalisé dans le cadre d'un projet de fin d'année en 3e année de licence informatique a l'INSA HDF par :

Noam Boutounas
Maxime Navellier
