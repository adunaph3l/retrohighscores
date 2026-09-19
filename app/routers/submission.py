from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Challenge, ScoreSubmission
from app.auth import get_current_user
from app.services.image_service import save_score_screenshot
from app.services.achievement_service import check_submission_achievements
from app.services.discord_service import notify_score_submitted
from app.services.scoring_service import get_challenge_leaderboard

router = APIRouter(prefix="/challenge", tags=["Submissions"])

@router.post("/{challenge_id}/submit")
async def submit_score(
    request: Request,
    challenge_id: int,
    score: int = Form(...),
    screenshot: UploadFile = File(...),
    comment: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge or not challenge.is_active or challenge.is_closed:
        raise HTTPException(status_code=400, detail="Ce challenge n'accepte plus de soumissions.")

    if score <= 0:
        return RedirectResponse(
            url=f"/challenge/{challenge_id}?msg=Le+score+doit+être+supérieur+à+0&msg_type=is-error",
            status_code=status.HTTP_303_SEE_OTHER
        )

    # Process and save screenshot image
    screenshot_url = save_score_screenshot(screenshot)
    if not screenshot_url:
        return RedirectResponse(
            url=f"/challenge/{challenge_id}?msg=Format+d'image+invalide+ou+fichier+trop+lourd&msg_type=is-error",
            status_code=status.HTTP_303_SEE_OTHER
        )

    now = datetime.utcnow()

    # Create submission
    sub = ScoreSubmission(
        challenge_id=challenge.id,
        user_id=current_user.id,
        score=score,
        screenshot_path=screenshot_url,
        comment=comment.strip() if comment else None,
        status="approved",
        created_at=now
    )
    db.add(sub)
    db.commit()

    # Check and award submission achievements (First Coin, Night Owl, Lucky Number, Sunday Warrior, Speedy)
    check_submission_achievements(db, current_user.id, now, score=score, challenge=challenge)

    # Determine current rank for notification
    leaderboard = get_challenge_leaderboard(db, challenge.id)
    rank = 1
    for entry in leaderboard:
        if entry["user"].id == current_user.id:
            rank = entry["rank"]
            break

    # Construct public image URL for Discord
    base_url = str(request.base_url).rstrip("/")
    full_screenshot_url = f"{base_url}{screenshot_url}"
    challenge_url = f"{base_url}/challenge/{challenge.id}"

    # Notify Discord
    game_name = challenge.game.name if challenge.game else "Jeu Rétro"
    await notify_score_submitted(
        username=current_user.username,
        game_name=game_name,
        score=score,
        rank=rank,
        screenshot_url=full_screenshot_url,
        site_url=challenge_url
    )

    return RedirectResponse(
        url=f"/challenge/{challenge_id}?msg=Score+enregistré+avec+succès+!+Votre+nom+figure+sur+la+borne+!&msg_type=is-success",
        status_code=status.HTTP_303_SEE_OTHER
    )