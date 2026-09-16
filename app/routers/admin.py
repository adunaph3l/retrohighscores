from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Game, Challenge, ScoreSubmission, ChallengeResult
from app.auth import get_current_admin
from app.services.scoring_service import close_challenge_and_award_points
from app.services.discord_service import notify_challenge_started, test_discord_webhook
from app.services.rawg_service import import_games_from_list

router = APIRouter(prefix="/admin", tags=["Administration"])
templates = Jinja2Templates(directory="app/templates")

@router.get("", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    active_challenge = (
        db.query(Challenge)
        .filter(Challenge.is_active == True, Challenge.is_closed == False)
        .first()
    )

    submissions = (
        db.query(ScoreSubmission)
        .order_by(ScoreSubmission.created_at.desc())
        .limit(30)
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="admin/dashboard.html",
        context={
            "current_user": admin,
            "active_challenge": active_challenge,
            "submissions": submissions,
            "flash_message": request.query_params.get("msg"),
            "flash_type": request.query_params.get("msg_type", "is-warning")
        }
    )

@router.get("/challenge/new", response_class=HTMLResponse)
async def new_challenge_form(
    request: Request,
    game_id: Optional[int] = None,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    games = db.query(Game).order_by(Game.name.asc()).all()
    now = datetime.now()
    default_start = now.strftime("%Y-%m-%dT%H:%M")
    default_end = (now + timedelta(days=7)).strftime("%Y-%m-%dT23:59")

    return templates.TemplateResponse(
        request=request,
        name="admin/challenge_form.html",
        context={
            "current_user": admin,
            "games": games,
            "selected_game_id": game_id,
            "default_start": default_start,
            "default_end": default_end
        }
    )

@router.post("/challenge/new")
async def create_challenge(
    request: Request,
    game_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    rules: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    notify_discord: Optional[str] = Form(None),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Jeu introuvable")

    try:
        dt_start = datetime.fromisoformat(start_date)
        dt_end = datetime.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Format de date invalide")

    # Deactivate existing active challenges if any
    db.query(Challenge).filter(Challenge.is_active == True).update({"is_active": False})

    new_challenge = Challenge(
        game_id=game.id,
        title=title.strip(),
        description=description.strip() or None,
        rules=rules.strip(),
        start_date=dt_start,
        end_date=dt_end,
        is_active=True,
        is_closed=False
    )
    db.add(new_challenge)
    db.commit()

    # Optional Discord Notification
    if notify_discord == "yes":
        base_url = str(request.base_url).rstrip("/")
        site_url = f"{base_url}/challenge/{new_challenge.id}"
        image_url = game.screenshot_image or game.cover_image
        if image_url and image_url.startswith("/"):
            image_url = f"{base_url}{image_url}"

        await notify_challenge_started(
            challenge_title=new_challenge.title,
            game_name=game.name,
            platform=game.platform,
            rules=new_challenge.rules,
            end_date_str=dt_end.strftime("%d/%m/%Y à %H:%M"),
            image_url=image_url,
            site_url=site_url
        )

    return RedirectResponse(
        url=f"/admin?msg=Nouveau+challenge+lancé+avec+succès+!&msg_type=is-success",
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.post("/challenge/{challenge_id}/close")
async def close_challenge_route(
    request: Request,
    challenge_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge introuvable")

    base_url = str(request.base_url).rstrip("/")
    site_url = f"{base_url}/challenge/{challenge.id}"

    await close_challenge_and_award_points(db, challenge, site_url=site_url)

    return RedirectResponse(
        url="/admin?msg=Challenge+clôturé+!+Les+points+ont+été+distribués+et+le+podium+annoncé.&msg_type=is-success",
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.get("/game-pool", response_class=HTMLResponse)
async def game_pool_page(
    request: Request,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    games = db.query(Game).order_by(Game.created_at.desc()).all()
    return templates.TemplateResponse(
        request=request,
        name="admin/game_pool.html",
        context={
            "current_user": admin,
            "games": games,
            "flash_message": request.query_params.get("msg"),
            "flash_type": request.query_params.get("msg_type", "is-warning")
        }
    )

@router.post("/game-pool/import-batch")
async def import_games_batch_route(
    request: Request,
    file: Optional[UploadFile] = File(None),
    text_list: Optional[str] = Form(None),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    combined_content = ""

    # Read uploaded text/csv file
    if file and file.filename:
        try:
            raw_bytes = await file.read()
            try:
                file_text = raw_bytes.decode("utf-8")
            except UnicodeDecodeError:
                file_text = raw_bytes.decode("latin-1", errors="ignore")
            combined_content += file_text + "\n"
        except Exception as e:
            return RedirectResponse(
                url=f"/admin/game-pool?msg=Erreur+de+lecture+du+fichier:+{e}&msg_type=is-error",
                status_code=status.HTTP_303_SEE_OTHER
            )

    # Append direct textarea content
    if text_list and text_list.strip():
        combined_content += text_list.strip() + "\n"

    if not combined_content.strip():
        return RedirectResponse(
            url="/admin/game-pool?msg=Veuillez+sélectionner+un+fichier+ou+coller+une+liste+de+jeux.&msg_type=is-warning",
            status_code=status.HTTP_303_SEE_OTHER
        )

    # Execute batch import & RAWG queries
    results = await import_games_from_list(db, combined_content)

    msg = f"Import terminé : {results['added']} jeux ajoutés ({results['rawg_found']} trouvés sur RAWG.io, {results['skipped']} déjà existants) !"
    return RedirectResponse(
        url=f"/admin/game-pool?msg={msg.replace(' ', '+')}&msg_type=is-success",
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.post("/game-pool/add-rawg")
async def add_game_from_rawg(
    request: Request,
    name: str = Form(...),
    platform: str = Form("Arcade / Rétro"),
    rawg_id: Optional[str] = Form(None),
    cover_image: Optional[str] = Form(None),
    screenshot_image: Optional[str] = Form(None),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    clean_rawg_id = int(rawg_id) if rawg_id and rawg_id.isdigit() else None
    new_game = Game(
        name=name.strip(),
        platform=platform.strip(),
        rawg_id=clean_rawg_id,
        cover_image=cover_image.strip() if cover_image else None,
        screenshot_image=screenshot_image.strip() if screenshot_image else None,
        in_random_pool=True
    )
    db.add(new_game)
    db.commit()

    return RedirectResponse(
        url="/admin/game-pool?msg=Jeu+ajouté+au+pool+avec+succès+!&msg_type=is-success",
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.post("/game-pool/add-manual")
async def add_game_manual(
    request: Request,
    name: str = Form(...),
    platform: str = Form("Arcade"),
    cover_image: Optional[str] = Form(None),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    new_game = Game(
        name=name.strip(),
        platform=platform.strip(),
        cover_image=cover_image.strip() if cover_image else None,
        in_random_pool=True
    )
    db.add(new_game)
    db.commit()

    return RedirectResponse(
        url="/admin/game-pool?msg=Jeu+personnalisé+ajouté+au+catalogue+!&msg_type=is-success",
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.post("/game/{game_id}/delete")
async def delete_game(
    game_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    game = db.query(Game).filter(Game.id == game_id).first()
    if game:
        db.delete(game)
        db.commit()
    return RedirectResponse(url="/admin/game-pool?msg=Jeu+supprimé.&msg_type=is-warning", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/submission/{sub_id}/delete")
async def delete_submission(
    sub_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    sub = db.query(ScoreSubmission).filter(ScoreSubmission.id == sub_id).first()
    if sub:
        db.delete(sub)
        db.commit()
    return RedirectResponse(url="/admin?msg=Score+supprimé.&msg_type=is-warning", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/discord/test")
async def trigger_discord_test(
    admin: User = Depends(get_current_admin)
):
    success = await test_discord_webhook()
    if success:
        return RedirectResponse(url="/admin?msg=Notification+Discord+envoyée+avec+succès+!&msg_type=is-success", status_code=status.HTTP_303_SEE_OTHER)
    else:
        return RedirectResponse(url="/admin?msg=Échec+de+l'envoi+Discord.+Vérifiez+votre+DISCORD_WEBHOOK_URL.&msg_type=is-error", status_code=status.HTTP_303_SEE_OTHER)