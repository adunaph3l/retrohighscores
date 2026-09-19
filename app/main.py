import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.database import engine, Base, SessionLocal
from app.config import UPLOAD_DIR, BASE_DIR
from app.services.achievement_service import seed_achievements
from app.models import Game
from app.routers import web, auth_routes, submission, admin, api_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("retro_app")

# Pre-seed classic arcade games if pool is empty
DEFAULT_ARCADE_GAMES = [
    {
        "name": "Metal Slug",
        "platform": "Neo-Geo / Arcade",
        "cover_image": "https://media.rawg.io/media/games/025/025586617a228f42a53239a53cb82db0.jpg",
        "screenshot_image": "https://media.rawg.io/media/screenshots/d43/d43521d9ef1fb0489953930058b72eeb.jpg",
        "in_random_pool": True
    },
    {
        "name": "Pac-Man",
        "platform": "Arcade",
        "cover_image": "https://media.rawg.io/media/games/6c9/6c9d72a9ef4599527f05bbbeeb5448bc.jpg",
        "screenshot_image": "https://media.rawg.io/media/screenshots/431/43193a20803a6bc026210f925e07a3c3.jpg",
        "in_random_pool": True
    },
    {
        "name": "Donkey Kong",
        "platform": "Arcade / NES",
        "cover_image": "https://media.rawg.io/media/games/c58/c586118d531a74d209117be2d37c8ee1.jpg",
        "screenshot_image": "https://media.rawg.io/media/screenshots/625/6250785160cb71b86d99df60e227a6f2.jpg",
        "in_random_pool": True
    },
    {
        "name": "Street Fighter II: The World Warrior",
        "platform": "Arcade / CPS-1",
        "cover_image": "https://media.rawg.io/media/games/3b8/3b8f6735e58849b2931a2388c3062634.jpg",
        "screenshot_image": "https://media.rawg.io/media/screenshots/5c3/5c37021eb1a47df125867946950220a2.jpg",
        "in_random_pool": True
    },
    {
        "name": "Tetris",
        "platform": "Game Boy / NES",
        "cover_image": "https://media.rawg.io/media/games/b2d/b2df31c77555627dd2c53f3e9a7e6ea3.jpg",
        "screenshot_image": "https://media.rawg.io/media/screenshots/b9f/b9fb6c5c0d2eb05ec2c6df4bf37b8641.jpg",
        "in_random_pool": True
    }
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Database Tables
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)

    # Safe schema migration for SQLite (e.g. avatar_image column)
    try:
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result.fetchall()]
            if "avatar_image" not in columns:
                logger.info("Migrating schema: adding avatar_image column to users table...")
                conn.execute(text("ALTER TABLE users ADD COLUMN avatar_image VARCHAR(500)"))
                conn.commit()
    except Exception as mig_err:
        logger.warning(f"Schema migration note: {mig_err}")

    # Seed base achievements & games
    db = SessionLocal()
    try:
        seed_achievements(db)

        # Seed games if empty
        if db.query(Game).count() == 0:
            for g_data in DEFAULT_ARCADE_GAMES:
                db.add(Game(**g_data))
            db.commit()
            logger.info("Default arcade game pool seeded.")
    finally:
        db.close()

    yield

app = FastAPI(
    title="Retro High Scores",
    description="Plateforme auto-hébergée rétro de challenges et high scores d'arcade",
    lifespan=lifespan
)

# Mount Static Files
static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Mount Uploads
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Mount Routers
app.include_router(web.router)
app.include_router(auth_routes.router)
app.include_router(submission.router)
app.include_router(admin.router)
app.include_router(api_routes.router)

# Space Invader Favicon
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(static_dir / "img" / "favicon.svg", media_type="image/svg+xml")

# Retro 404 Error Page
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    return templates.TemplateResponse(
        request=request,
        name="base.html",
        context={
            "current_user": None,
            "flash_message": "404 - GAME OVER : Cette page n'existe pas dans la salle d'arcade !",
            "flash_type": "is-error"
        },
        status_code=404
    )