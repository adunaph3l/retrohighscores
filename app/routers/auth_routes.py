from datetime import timedelta
from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.auth import get_password_hash, verify_password, create_access_token, get_current_user_optional
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["Auth"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, next: str = "", db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if user:
        return RedirectResponse(url=next or "/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "current_user": None,
            "next_url": next,
            "flash_message": request.query_params.get("msg"),
            "flash_type": request.query_params.get("msg_type", "is-warning")
        }
    )

@router.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form(""),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username.ilike(username.strip())).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "current_user": None,
                "next_url": next,
                "flash_message": "Pseudo ou mot de passe incorrect.",
                "flash_type": "is-error"
            },
            status_code=400
        )

    # Generate Token
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    redirect_url = next if next and next.startswith("/") else "/"
    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    # Set Cookie with secure options compatible with NPMPlus reverse proxy
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        samesite="lax"
    )
    return response

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if user:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={
            "current_user": None
        }
    )

@router.post("/register")
async def register_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    clean_username = username.strip()
    clean_email = email.strip().lower()

    if len(clean_username) < 3 or len(clean_username) > 20:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "current_user": None,
                "flash_message": "Le pseudo doit faire entre 3 et 20 caractères.",
                "flash_type": "is-error"
            },
            status_code=400
        )

    if len(password) < 6:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "current_user": None,
                "flash_message": "Le mot de passe doit faire au moins 6 caractères.",
                "flash_type": "is-error"
            },
            status_code=400
        )

    # Check existing user
    if db.query(User).filter(User.username.ilike(clean_username)).first():
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "current_user": None,
                "flash_message": "Ce pseudo est déjà utilisé par un autre joueur.",
                "flash_type": "is-error"
            },
            status_code=400
        )

    if db.query(User).filter(User.email == clean_email).first():
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "current_user": None,
                "flash_message": "Cette adresse email est déjà enregistrée.",
                "flash_type": "is-error"
            },
            status_code=400
        )

    # First user registered is automatically Admin!
    total_users = db.query(User).count()
    is_admin = (total_users == 0)

    new_user = User(
        username=clean_username,
        email=clean_email,
        hashed_password=get_password_hash(password),
        is_admin=is_admin,
        total_points=0
    )
    db.add(new_user)
    db.commit()

    # Log user in directly
    access_token = create_access_token(
        data={"sub": new_user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        samesite="lax"
    )
    return response

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response