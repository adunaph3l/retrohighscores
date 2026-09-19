# 🕹️ Retro High Scores - Arcade & Retro Gaming Platform

Application web auto-hébergée au style **NES rétro 8-bit** conçue pour organiser des défis de jeux vidéo, soumettre des high scores avec capture d'écran de preuve, et concourir au **Hall of Fame** grâce à un système de points et de trophées.

Optimisée pour **Unraid** (Docker Compose), avec support natif pour le reverse proxy **NPMPlus** (SSL HTTPS) et notifications automatiques vers **Discord**.

---

## 🌟 Fonctionnalités Principales

- **Design 100% Rétro avec NES.css** :
  - Utilisation de la bibliothèque [NES.css](https://nostalgic-css.github.io/NES.css/) et de la police *"Press Start 2P"*.
  - **Entièrement Responsive** : Adaptation sur-mesure pour smartphones et tablettes (tableaux scrollables, menu tiroir tactile, conteneurs ajustés).
  - **Mode CRT Scanlines** : Effet d'écran cathodique rétro activable en un clic (`📺 CRT: ON/OFF`).
- **Ambiance Sonore 8-bit (Web Audio API)** :
  - Bruitages authentiques synthétisés en temps réel par le navigateur (bruitage de pièce de monnaie Mario/arcade, 1-Up, Game Over, clics, roulette).
  - Zéro fichier audio lourd à télécharger, bouton Mute persistant dans le navigateur.
- **Easter Eggs & Secrets** :
  - Intégration du légendaire **Code Konami** (`↑ ↑ ↓ ↓ ← → ← → B A`) débloquant une fanfare de victoire, une pluie de confettis pixels et un **trophée secret** sur le profil du joueur !
- **Challenges Périodiques & Classement en Direct** :
  - Page d'accueil dédiée au challenge en cours avec compte à rebours interactif.
  - **Récupération automatique des captures d'écran et jaquettes** de jeux sur Internet via l'API **RAWG.io**.
  - **Pool de Jeux & Roulette de Tirage Aléatoire** : L'administrateur peut enregistrer un catalogue de jeux et lancer un tirage au sort avec animation de machine à sous pour désigner le prochain jeu du défi !
  - Classement en direct avec podium (🥇 1er, 🥈 2e, 🥉 3e) et modal d'agrandissement pour inspecter les captures d'écran des participants.
- **Soumission Sécurisée avec Preuve Photo** :
  - Compte joueur obligatoire avec hachage Bcrypt.
  - Traitement intelligent des photos smartphone avec **Pillow** (correction automatique de la rotation EXIF et optimisation en WebP léger).
- **Système de Trophées (Achievements)** :
  - Salle des trophées sur chaque profil joueur avec badges déblocables (Première Pièce, Sur le Podium, Champion, Habitué du Stick, Joueur Nocturne, Code Konami...).
- **Attribution des Points & Hall of Fame** :
  - À la clôture du défi, les points sont attribués : 
    - 🥇 1er : 100 pts | 🥈 2e : 75 pts | 🥉 3e : 50 pts | 4e : 35 pts | 5e : 25 pts | 6e-10e : 15 pts | Tout autre score : 10 pts.
  - Classement général permanent (Panthéon des joueurs).
- **Notifications Discord Automatiques (Webhook)** :
  - 🎮 **Lancement d'un challenge** : annonce avec image du jeu, règles et compte à rebours.
  - 🔥 **Nouveau score soumis** : annonce du score réalisé et du rang actuel avec la photo de preuve.
  - 🏁 **Clôture du challenge** : annonce du podium final et des points gagnés.

---

## 🚀 Déploiement sur Unraid

### 1. Préparation du dossier sur Unraid

Copiez ce dossier complet dans votre partage `appdata` sur Unraid, par exemple :
`/mnt/user/appdata/retro-highscores`

### 2. Configuration du fichier `.env`

Dans le dossier, copiez le fichier d'exemple :
```bash
cp .env.example .env
```
Éditez le fichier `env.example` avec vos paramètres et renommez le en `.env`:
- `SECRET_KEY` : une clé secrète aléatoire de votre choix.
- `RAWG_API_KEY` : votre clé gratuite obtenue sur [RAWG.io/apidocs](https://rawg.io/apidocs) (permet la recherche instantanée et la récupération des jaquettes/screenshots).
- `DISCORD_WEBHOOK_URL` : l'URL de votre webhook de salon Discord.

### 3. Lancement du conteneur Docker

Depuis l'interface Unraid (via le plugin **Docker Compose Manager**) ou en SSH dans le dossier :
```bash
docker compose up -d --build
```
L'application démarre sur le port **`8080`** de votre serveur Unraid.

---

## 🔒 Configuration du Reverse Proxy (NPMPlus / Nginx Proxy Manager)

Pour exposer votre site de manière sécurisée en HTTPS depuis l'extérieur :

1. Dans **NPMPlus**, cliquez sur **"Add Proxy Host"**.
2. Remplissez l'onglet **Details** :
   - **Domain Names** : votre nom de domaine (ex: `scores.mon-domaine.fr`).
   - **Scheme** : `http`
   - **Forward Hostname / IP** : l'adresse IP locale de votre serveur Unraid (ex: `192.168.1.100`).
   - **Forward Port** : `8080`
   - Cochez **"Block Common Exploits"** et **"Websockets Support"**.
3. Remplissez l'onglet **SSL** :
   - Sélectionnez ou demandez un certificat **Let's Encrypt**.
   - Cochez **"Force SSL"** et **"HTTP/2 Support"**.
4. Cliquez sur **Save**. Votre site est accessible immédiatement en HTTPS !

---

## 👑 Premier Démarrage & Compte Administrateur

1. Rendez-vous sur le site (ou votre nom de domaine).
2. Cliquez sur **"Inscription"** et créez votre compte joueur.  
   > 💡 **Astuce** : Le **tout premier compte créé** sur le site reçoit automatiquement le rôle **Administrateur** !
3. En tant qu'administrateur, un bouton **"⚙️ Admin"** apparaîtra dans le menu supérieur. Vous pourrez :
   - Tester la liaison avec votre Webhook Discord d'un simple clic.
   - **Importer en masse vos jeux** : téléversez un simple fichier `.txt` ou `.csv` (ou collez votre liste) dans l'onglet **"Pool de Jeux"**. L'application interroge automatiquement **RAWG.io** pour récupérer jaquettes HD et captures d'écran pour chacun d'eux !
   - Tirer un jeu au sort avec la roulette arcade et lancer un nouveau challenge officiel !
   - Clôturer les challenges à leur échéance pour déclencher l'attribution des points et l'annonce du podium sur Discord.

---

## 📁 Persistance des Données

Sur Unraid, toutes les données restent pérennes lors des mises à jour du conteneur grâce aux deux volumes mappés :
- `/app/data` : Base de données SQLite (mode WAL haute performance).
- `/app/uploads` : Captures d'écran des scores et images des jeux.

---

## 🎮 Easter Egg

Essayez la combinaison de touches suivante sur votre clavier :  
`Haut, Haut, Bas, Bas, Gauche, Droite, Gauche, Droite, B, A` !

---

## 📝 Historique des Modifications

### 19/09/2026
- **Gestion des utilisateurs dans l'administration** : Affichage dans le tableau de bord d'administration de la liste complète des joueurs inscrits avec leurs avatars, adresses email, total de points au Hall of Fame, dates d'inscription et boutons d'action permettant la promotion ou rétrogradation du rôle d'administrateur en toute sécurité.
- **Système de notifications par Email au design rétro NES** : Notification automatique par email de tous les joueurs inscrits lors des événements clés de la borne d'arcade (lancement d'un nouveau challenge officiel, nouveau high score soumis par un joueur, et clôture de challenge avec annonce du podium et distribution des points). Les courriels adoptent un design soigné 8-bit rétro identique à l'ambiance du site et contiennent les mêmes informations que les alertes Discord (jaquette, règles, photo de preuve de score, médailles).
- **Configuration SMTP & Outil de test d'envoi** : Panneau de configuration complet du serveur d'envoi SMTP directement accessible depuis la console d'administration (hôte, port, identifiants, sécurité STARTTLS/SSL, adresse et nom d'expéditeur, sélection des événements à notifier) et bouton de test d'envoi d'email rétro intégré pour vérifier instantanément la connectivité SMTP.
- **Correction des correspondances RAWG.io** : Ajout d'une page d'édition par jeu dans le catalogue de l'administration. Elle permet de corriger une mauvaise association RAWG.io grâce à une recherche en direct avec prévisualisation des jaquettes et captures d'écran, ou d'ajuster manuellement les informations et URLs des images.
- **Photo de profil / Avatar personnalisé** : Les joueurs peuvent désormais téléverser une photo de profil depuis leur page joueur. Le système gère tous les formats d'images (y compris HEIC/HEIF Apple iPhone), recadre automatiquement en carré centré et convertit en WebP optimisé. L'avatar apparaît sur le profil, dans la barre de navigation et sur tous les tableaux de classement.
- **Nouveaux succès secrets masqués** : Ajout de trophées cachés dont le titre et la description restent masqués (« ??? ») tant qu'ils n'ont pas été débloqués, invitant les joueurs à explorer des actions insolites ou à les obtenir par surprise (scores insolites, horaires décalés, easter eggs, avatar personnalisé, etc.).
- **Ajustement de l'alignement du tableau d'administration** : Amélioration du design des badges de plateformes dans le catalogue du pool de jeux pour garantir un calibrage parfait des colonnes sans aucun débordement.

### 16/09/2026
- **Prise en charge des images HEIC / HEIF (iPhone)** : Support des photos prises avec un iPhone d'Apple. Les fichiers HEIC/HEIF envoyés par les joueurs sont automatiquement redressés selon leur orientation EXIF et convertis côté serveur en WebP optimisé, garantissant un affichage parfait sur tous les navigateurs (Chrome, Firefox, Safari, Edge, Android, PC).

### 04/09/2026
- **Favicon Space Invader** : Ajout d'un favicon en pixel-art représentant le mythique Space Invader rétro et configuration de la route `/favicon.ico`.
- **Import en masse de jeux** : Ajout de la fonctionnalité permettant de téléverser un fichier (`.txt`, `.csv`) ou de coller une liste de jeux dans l'administration, avec recherche et récupération automatique des jaquettes et captures d'écran sur l'API RAWG.io.
- **Correction compatibilité templates** : Résolution de l'incompatibilité avec les versions récentes de Starlette/FastAPI pour le rendu des pages HTML.
- **Lancement initial** : Création de la plateforme web rétro avec NES.css, authentification, challenges périodiques, roulette de tirage au sort, système de trophées déblocables, Hall of Fame, notifications Webhook Discord et bruitages Web Audio 8-bit.
