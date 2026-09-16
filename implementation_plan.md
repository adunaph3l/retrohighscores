# Plan d'implémentation : Plateforme Rétro de High Scores

Création d'une application web auto-hébergée complète au look rétro NES pour organiser des challenges de jeux vidéo, soumettre des high scores avec capture d'écran de preuve, et gérer des classements par challenge et globaux avec attribution de points.
Le projet sera optimisé pour un déploiement direct sous Unraid via Docker Compose et configuré pour le reverse proxy NPMPlus avec certificat SSL.

---

## Architecture Technique

- **Backend & Serveur** : **Python 3.11** avec **FastAPI**, **Jinja2** pour le rendu serveur, et **Uvicorn**.
- **Base de données** : **SQLite avec WAL (Write-Ahead Logging)** via **SQLAlchemy**, ultra-léger et zéro maintenance sur Unraid (stocké dans `/mnt/user/appdata/retro-highscores/data`).
- **Design & UI** : 
  - **NES.css** (https://nostalgic-css.github.io/NES.css/) + police pixel *"Press Start 2P"*.
  - CSS sur-mesure pour garantir un **responsive design irréprochable sur smartphone** (ajustement des conteneurs, tableaux défilables / cartes mobiles, boutons tactiles).
  - Effet CRT Scanlines rétro activable/désactivable.
- **Audio Rétro 8-bit (Easter Egg & Immersion)** :
  - Synthétiseur audio Web Audio API natif (bruitages 8-bit authentiques : son de pièce de monnaie lors d'un score soumis, son 1-Up à la connexion, son Game Over, son de clic). Zéro fichier audio lourd à charger, bouton Mute persistant.
  - Konami Code (`↑ ↑ ↓ ↓ ← → ← → B A`) déclenchant une animation et un trophée secret.
- **Gestion des Images & API Jeux** :
  - Client API **RAWG.io** pour récupérer automatiquement la jaquette et des captures d'écran en jeu dès qu'un challenge est configuré.
  - Traitement et optimisation automatique des captures d'écran soumises par les joueurs avec **Pillow** (redimensionnement intelligent, rotation EXIF pour photos smartphone, compression WebP/JPEG pour préserver l'espace disque sur Unraid).
- **Déploiement Unraid** :
  - `Dockerfile` optimisé et `docker-compose.yml` prêt à l'emploi.
  - Configuration transparente pour reverse proxy **NPMPlus** (headers `X-Forwarded-Proto`, SSL, etc.).

---

## Modèle de Données (SQLite)

1. **User** : ID, username, email, hashed_password, is_admin, total_points, avatar_style, created_at.
2. **Game** : ID, name, platform, rawg_id, cover_image, screenshot_image, description.
3. **Challenge** : ID, game_id, title, description, start_date, end_date, is_active, is_closed, points_awarded.
4. **ScoreSubmission** : ID, challenge_id, user_id, score, screenshot_path, status (`approved`, `pending`, `rejected`), created_at.
5. **ChallengeResult** : ID, challenge_id, user_id, rank, points, final_score (historique après clôture).

---

## Fonctionnalités Clés

### 1. Authentification & Profils
- Inscription et connexion sécurisées (hachage de mot de passe Bcrypt, cookies de session sécurisés compatibles HTTPS/NPMPlus).
- Rôles : Joueur et Administrateur (premier compte créé devient automatiquement Admin ou défini par variable d'environnement).
- Page de profil : historique des participations, trophées remportés, total des points.

### 2. Challenge Actif & Classement Périodique
- Page d'accueil dédiée au challenge en cours avec compte à rebours rétro (jours/heures/minutes restants).
- Affichage de la capture d'écran du jeu récupérée automatiquement via RAWG.io.
- Classement en direct avec les scores enregistrés, médailles rétro (🥇 1er, 🥈 2ème, 🥉 3ème).
- Modal d'agrandissement pour inspecter les captures d'écran de preuve des joueurs.
- Formulaire de soumission de score avec prévisualisation immédiate de la capture d'écran.

### 3. Clôture & Système de Points Globaux
- Calcul automatique ou manuel par l'administrateur à la date de fin du challenge :
  - 1er : 100 points
  - 2ème : 75 points
  - 3ème : 50 points
  - 4ème : 35 points
  - 5ème : 25 points
  - 6ème au 10ème : 15 points
  - Tous les autres participants : 10 points (points de participation)
- Mise à jour du classement général permanent (Hall of Fame).

### 4. Archives des Challenges Passés
- Historique des challenges terminés avec podium, score vainqueur et screenshots archivés.

### 5. Administration
- Création / édition de challenges avec recherche instantanée de jeux (RAWG.io) pour pré-remplir les données et l'image.
- Validation / modération des scores si nécessaire.
- Bouton de clôture et attribution des points.

---

## Structure des Fichiers Proposée

```
c:/Users/islil/Documents/test-vibe/HighScores/
├── app/
│   ├── __init__.py
│   ├── main.py                  # Application FastAPI, gestion des erreurs, middlewares
│   ├── database.py              # Configuration SQLite WAL & sessions SQLAlchemy
│   ├── models.py                # Modèles SQLAlchemy (User, Game, Challenge, Score, Result)
│   ├── schemas.py               # Schémas de validation Pydantic
│   ├── auth.py                  # Sécurité, JWT/Session cookie, hash Bcrypt
│   ├── services/
│   │   ├── __init__.py
│   │   ├── rawg_service.py      # Recherche et récupération d'images RAWG.io + fallback
│   │   ├── image_service.py     # Optimisation & stockage des screenshots Pillow
│   │   └── scoring_service.py   # Calcul des classements & distribution des points
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── web.py               # Routes d'affichage (HTML/Jinja2)
│   │   ├── auth_routes.py       # Inscription, connexion, déconnexion
│   │   ├── submission.py        # Soumission de high scores et upload
│   │   └── admin.py             # Gestion des challenges et modération
│   ├── static/
│   │   ├── css/
│   │   │   ├── nes.min.css      # NES.css local pour résilience hors-ligne
│   │   │   └── custom.css       # Responsive design mobile, scanlines CRT, animations
│   │   ├── js/
│   │   │   ├── retro-audio.js   # Bruitages 8-bit Web Audio synthétisés
│   │   │   ├── easter-eggs.js   # Konami code, scanlines toggle, surprises rétro
│   │   │   └── main.js          # Menu mobile, preview d'upload, modals
│   │   └── img/
│   │       └── default-game.png # Image par défaut pixel-art
│   └── templates/
│       ├── base.html            # Layout principal NES.css, nav, footer, audio player
│       ├── index.html           # Page d'accueil : Challenge actif & Top scores
│       ├── challenge_detail.html# Vue détaillée du challenge avec soumission
│       ├── archive.html         # Challenges passés et podiums
│       ├── leaderboard.html     # Classement général (Hall of Fame)
│       ├── profile.html         # Profil utilisateur & trophées
│       ├── login.html           # Connexion style cartouche rétro
│       ├── register.html        # Inscription
│       └── admin/
│           ├── dashboard.html   # Tableau de bord administrateur
│           └── challenge_form.html # Création/édition de challenge avec recherche RAWG
├── Dockerfile                   # Build de l'image Docker optimisée
├── docker-compose.yml           # Déploiement Unraid clé en main
├── .env.example                 # Modèle des variables d'environnement
├── requirements.txt             # Dépendances Python
└── README.md                    # Guide complet de déploiement pour Unraid & NPMPlus
```

---

## Plan de Vérification

### 1. Tests Automatisés
- Tests unitaires de la logique de calcul des points (`scoring_service`).
- Tests d'authentification (hashage de mot de passe, tokens de session).
- Tests de création de challenge et de soumission de scores avec simulation d'upload d'image.

### 2. Validation Manuelle & Responsive
- Vérification du rendu sur mobile (émulation Chrome DevTools iPhone/Android) : navigation hamburger, tableaux scrollables, boutons NES adaptés au tactile.
- Test de l'effet sonore Web Audio et du code Konami.
- Test de la récupération de visuels de jeux via RAWG.io.
- Vérification du fichier `docker-compose.yml` et de la configuration pour NPMPlus.
