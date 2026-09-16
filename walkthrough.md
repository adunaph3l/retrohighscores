# Walkthrough : Plateforme Rétro de High Scores

L'ensemble des fichiers du projet a été développé, validé et structuré pour un déploiement clé en main sur **Unraid** avec **Docker Compose** et intégration avec le reverse proxy **NPMPlus**.

---

## 🕹️ Ce qui a été réalisé

### 1. Design & Expérience Utilisateur Rétro
- **CSS NES.css Officielle** : Intégrée en local (`/static/css/nes.min.css`) pour une résilience maximale hors-ligne.
- **Responsive Mobile Optimisé** : Feuilles de styles sur-mesure (`retro-custom.css`) avec adaptation des polices, tableaux avec barres de défilement horizontal (`.table-responsive`), conteneurs compacts et menu de navigation tactile.
- **Effet CRT Cathodique** : Bouton `📺 CRT: ON/OFF` appliquant des scanlines rétro animées.
- **Synthétiseur Audio 8-bit (Web Audio API)** : Bruitages temps réel de pièces de monnaie, 1-Up, Game Over, clics et roulette sans aucun fichier MP3 externe à charger.
- **Code Konami Secret** : Détection de la séquence `↑ ↑ ↓ ↓ ← → ← → B A` avec fanfare, pluie de confettis pixels et déblocage du trophée secret.

### 2. Gestion des Challenges & Tirage Aléatoire
- **Spotlight du Challenge Actif** : Page d'accueil avec jaquette/screenshot du jeu, compte à rebours interactif, règles officielles et Top 5 en direct.
- **Pool de Jeux & Roulette de Sélection** :
  - L'administrateur gère un catalogue de jeux candidats.
  - Recherche instantanée et récupération automatique des jaquettes et captures d'écran via l'API **RAWG.io**.
  - Roulette arcade avec bruitage pour tirer au sort le prochain jeu du challenge.
- **Soumission de Score avec Preuve** :
  - Inscription/connexion obligatoire.
  - Upload de capture d'écran avec prévisualisation immédiate et optimisation via **Pillow** (correction automatique de la rotation smartphone EXIF).
  - Modal d'agrandissement pour inspecter les captures d'écran des scores sur le classement.

### 3. Système de Trophées & Hall of Fame
- **Salle des Trophées** : Badges rétro visibles sur le profil de chaque joueur (débloqués avec couleurs vives, verrouillés en grisé avec instructions pour les remporter).
- **Attribution des Points** :
  - Clôture de challenge avec attribution automatique des points (1er: 100, 2e: 75, 3e: 50, 4e: 35, 5e: 25, 6-10e: 15, participation: 10).
  - Classement général permanent (Hall of Fame) avec statistiques de victoires et trophées.

### 4. Notifications Discord (Webhook)
- Annonce automatique lors du lancement d'un nouveau challenge (image du jeu, dates, règles).
- Annonce lors de la soumission d'un nouveau score avec lien et capture de preuve.
- Annonce lors de la clôture avec récapitulatif du podium final (1er, 2e, 3e).
- Bouton de test direct depuis la console d'administration.

---

## 📂 Structure du Répertoire Créé

```
HighScores/
├── app/
│   ├── main.py                  # Point d'entrée FastAPI & initialisation BDD
│   ├── config.py                # Configuration (.env) & barème des points
│   ├── database.py              # Connexion SQLite avec optimisation WAL
│   ├── models.py                # Modèles SQLAlchemy (User, Game, Challenge, Score, Achievement)
│   ├── auth.py                  # Sécurité Bcrypt & sessions JWT
│   ├── services/
│   │   ├── discord_service.py   # Webhook Discord (lancement, scores, podium)
│   │   ├── rawg_service.py      # Recherche auto et récupération d'images de jeux
│   │   ├── image_service.py     # Traitement et compression des captures (Pillow)
│   │   ├── scoring_service.py   # Calcul des classements & distribution des points
│   │   └── achievement_service.py # Gestion des trophées déblocables
│   ├── routers/
│   │   ├── web.py               # Pages HTML (Accueil, Challenge, Archives, Leaderboard, Profil)
│   │   ├── auth_routes.py       # Inscription, Connexion, Déconnexion
│   │   ├── submission.py        # Upload de score et validation
│   │   ├── admin.py             # Console d'administration et modération
│   │   └── api_routes.py        # Endpoints API (RAWG search, Roulette pool, Konami)
│   ├── static/
│   │   ├── css/                 # nes.min.css & retro-custom.css
│   │   ├── js/                  # retro-audio.js, easter-eggs.js, main.js
│   │   └── img/                 # default-game.svg
│   └── templates/               # Templates Jinja2 (SSR avec NES.css)
│       └── admin/               # Templates d'administration & pool de jeux
├── tests/
│   └── test_logic.py            # Tests unitaires de la logique métier (100% OK)
├── Dockerfile                   # Image Python 3.11-slim optimisée
├── docker-compose.yml           # Déploiement Unraid clé en main
├── .env.example                 # Modèle des variables d'environnement
├── requirements.txt             # Dépendances Python
└── README.md                    # Guide complet Unraid & NPMPlus
```

---

## 🚀 Prochaines Étapes pour le Déploiement

1. **Copiez le dossier** `HighScores` sur votre Unraid (ex: `/mnt/user/appdata/retro-highscores`).
2. **Copiez `.env.example` en `.env`** et insérez :
   - Votre clé `RAWG_API_KEY` (gratuite sur [rawg.io/apidocs](https://rawg.io/apidocs)).
   - Votre URL `DISCORD_WEBHOOK_URL` (salon Discord où poster les annonces).
3. **Lancez le conteneur** :
   ```bash
   docker compose up -d --build
   ```
4. **Configurez NPMPlus** :
   - Pointez votre sous-domaine vers l'IP de votre serveur Unraid, port `8080`.
   - Activez le certificat SSL Let's Encrypt ("Force SSL").
5. **Créez le premier compte sur le site** : il sera automatiquement nommé **Administrateur** !
