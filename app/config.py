import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Database
# If running in docker, data is in /app/data, otherwise in ./data
DEFAULT_DB_DIR = BASE_DIR / "data"
DEFAULT_DB_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_DIR}/highscores.db")

# Uploads
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads")))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
(UPLOAD_DIR / "scores").mkdir(parents=True, exist_ok=True)
(UPLOAD_DIR / "games").mkdir(parents=True, exist_ok=True)
(UPLOAD_DIR / "avatars").mkdir(parents=True, exist_ok=True)

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "retro-secret-arcade-token-change-in-prod-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30  # 30 days

# External Services
RAWG_API_KEY = os.getenv("RAWG_API_KEY", "").strip()
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()

# Admin initial credentials
ADMIN_INITIAL_USERNAME = os.getenv("ADMIN_INITIAL_USERNAME", "admin")
ADMIN_INITIAL_PASSWORD = os.getenv("ADMIN_INITIAL_PASSWORD", "admin1234")

# Points distribution for challenge rankings
# 1st: 100, 2nd: 75, 3rd: 50, 4th: 35, 5th: 25, 6th-10th: 15, participation: 10
POINTS_DISTRIBUTION = {
    1: 100,
    2: 75,
    3: 50,
    4: 35,
    5: 25,
    6: 15,
    7: 15,
    8: 15,
    9: 15,
    10: 15
}
PARTICIPATION_POINTS = 10