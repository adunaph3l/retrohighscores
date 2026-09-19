from typing import List
from fastapi import APIRouter, Request, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Game
from app.auth import get_current_user_optional
from app.services.achievement_service import unlock_achievement
from app.services.rawg_service import search_games

router = APIRouter(prefix="/api", tags=["API"])

@router.get("/easter-egg/konami")
async def unlock_konami(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if user:
        unlocked = unlock_achievement(db, user.id, "konami_master")
        return {"status": "ok", "unlocked": unlocked, "message": "Konami code achievement awarded!"}
    return {"status": "guest", "message": "Konami code detected, connectez-vous pour conserver le trophée !"}

@router.get("/easter-egg/crt")
async def unlock_crt(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if user:
        unlocked = unlock_achievement(db, user.id, "crt_master")
        return {"status": "ok", "unlocked": unlocked, "message": "CRT achievement awarded!"}
    return {"status": "guest"}

@router.get("/games/search")
async def api_search_games(q: str = Query(..., min_length=1)):
    results = await search_games(q)
    return results

@router.get("/games/random-pool")
async def api_random_pool(db: Session = Depends(get_db)):
    games = db.query(Game).filter(Game.in_random_pool == True).all()
    return [
        {
            "id": g.id,
            "name": g.name,
            "platform": g.platform,
            "cover_image": g.cover_image or "/static/img/default-game.svg"
        }
        for g in games
    ]