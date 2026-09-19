from datetime import datetime
from fastapi import APIRouter, Request, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models import User, Game, Challenge, ScoreSubmission, Achievement, UserAchievement, ChallengeResult
from app.auth import get_current_user_optional, get_current_user
from app.services.scoring_service import get_challenge_leaderboard
from app.services.image_service import save_avatar_image
from app.services.achievement_service import unlock_achievement

router = APIRouter(tags=["Web Pages"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)

    # Get the latest active, non-closed challenge
    challenge = (
        db.query(Challenge)
        .filter(Challenge.is_active == True, Challenge.is_closed == False)
        .order_by(Challenge.created_at.desc())
        .first()
    )

    leaderboard = []
    if challenge:
        leaderboard = get_challenge_leaderboard(db, challenge.id)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "current_user": user,
            "challenge": challenge,
            "leaderboard": leaderboard,
            "flash_message": request.query_params.get("msg"),
            "flash_type": request.query_params.get("msg_type", "is-warning")
        }
    )

@router.get("/challenge/{challenge_id}", response_class=HTMLResponse)
async def challenge_detail(request: Request, challenge_id: int, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge introuvable")

    leaderboard = get_challenge_leaderboard(db, challenge.id)

    return templates.TemplateResponse(
        request=request,
        name="challenge_detail.html",
        context={
            "current_user": user,
            "challenge": challenge,
            "leaderboard": leaderboard,
            "flash_message": request.query_params.get("msg"),
            "flash_type": request.query_params.get("msg_type", "is-warning")
        }
    )

@router.get("/archive", response_class=HTMLResponse)
async def archive_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    # Get all closed challenges, newest first
    challenges = (
        db.query(Challenge)
        .filter(Challenge.is_closed == True)
        .order_by(Challenge.end_date.desc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="archive.html",
        context={
            "current_user": user,
            "challenges": challenges,
            "flash_message": request.query_params.get("msg"),
            "flash_type": request.query_params.get("msg_type", "is-warning")
        }
    )

@router.get("/leaderboard", response_class=HTMLResponse)
async def leaderboard_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)

    # Fetch users ordered by total_points descending
    users_db = db.query(User).order_by(desc(User.total_points)).all()

    users_data = []
    for u in users_db:
        trophies_count = db.query(UserAchievement).filter(UserAchievement.user_id == u.id).count()
        wins_count = db.query(ChallengeResult).filter(ChallengeResult.user_id == u.id, ChallengeResult.rank == 1).count()
        participations_count = db.query(ChallengeResult).filter(ChallengeResult.user_id == u.id).count()

        users_data.append({
            "id": u.id,
            "username": u.username,
            "avatar_image": u.avatar_image,
            "total_points": u.total_points,
            "trophies_count": trophies_count,
            "wins_count": wins_count,
            "participations_count": participations_count
        })

    return templates.TemplateResponse(
        request=request,
        name="leaderboard.html",
        context={
            "current_user": user,
            "users": users_data,
            "flash_message": request.query_params.get("msg"),
            "flash_type": request.query_params.get("msg_type", "is-warning")
        }
    )

@router.get("/profile/{username}", response_class=HTMLResponse)
async def profile_page(request: Request, username: str, db: Session = Depends(get_db)):
    current_user = get_current_user_optional(request, db)
    profile_user = db.query(User).filter(User.username.ilike(username)).first()
    if not profile_user:
        raise HTTPException(status_code=404, detail="Joueur introuvable")

    # Global Rank
    higher_users = db.query(User).filter(User.total_points > profile_user.total_points).count()
    user_rank = higher_users + 1

    # Achievements
    all_achievements = db.query(Achievement).all()
    user_achs = db.query(UserAchievement).filter(UserAchievement.user_id == profile_user.id).all()
    unlocked_ids = {ua.achievement_id for ua in user_achs}

    # Submissions history
    user_submissions = (
        db.query(ScoreSubmission)
        .filter(ScoreSubmission.user_id == profile_user.id)
        .order_by(ScoreSubmission.created_at.desc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "current_user": current_user,
            "profile_user": profile_user,
            "user_rank": user_rank,
            "all_achievements": all_achievements,
            "unlocked_ids": unlocked_ids,
            "unlocked_count": len(unlocked_ids),
            "total_achievements_count": len(all_achievements),
            "user_submissions": user_submissions,
            "flash_message": request.query_params.get("msg"),
            "flash_type": request.query_params.get("msg_type", "is-warning")
        }
    )

@router.post("/profile/avatar")
async def upload_avatar(
    request: Request,
    avatar: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic", ".heif"}
    filename = (avatar.filename or "").lower()

    if not any(filename.endswith(ext) for ext in allowed_extensions):
        return RedirectResponse(
            url=f"/profile/{current_user.username}?msg=Format+non+supporté.+Utilisez+JPG,+PNG,+WebP+ou+HEIC.&msg_type=is-error",
            status_code=status.HTTP_303_SEE_OTHER
        )

    avatar_url = save_avatar_image(avatar)
    if not avatar_url:
        return RedirectResponse(
            url=f"/profile/{current_user.username}?msg=Erreur+lors+du+traitement+de+l'image.&msg_type=is-error",
            status_code=status.HTTP_303_SEE_OTHER
        )

    current_user.avatar_image = avatar_url
    db.commit()

    # Unlock custom avatar achievement
    unlock_achievement(db, current_user.id, "custom_avatar")

    return RedirectResponse(
        url=f"/profile/{current_user.username}?msg=Photo+de+profil+mise+à+jour+avec+succès+!&msg_type=is-success",
        status_code=status.HTTP_303_SEE_OTHER
    )