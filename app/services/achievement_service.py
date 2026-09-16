from datetime import datetime
import logging
from sqlalchemy.orm import Session
from app.models import Achievement, UserAchievement, User, ScoreSubmission, ChallengeResult

logger = logging.getLogger("achievement_service")

DEFAULT_ACHIEVEMENTS = [
    {
        "code": "first_coin",
        "title": "Première Pièce",
        "description": "Avoir soumis son tout premier high score dans la salle d'arcade.",
        "icon": "coin",
        "category": "participation",
        "badge_class": "is-warning"
    },
    {
        "code": "podium_finish",
        "title": "Sur le Podium",
        "description": "Atteindre le top 3 lors de la clôture d'un challenge.",
        "icon": "star",
        "category": "performance",
        "badge_class": "is-primary"
    },
    {
        "code": "champion",
        "title": "Champion Arcade",
        "description": "Décrocher la 1ère place d'un challenge officiel !",
        "icon": "trophy",
        "category": "performance",
        "badge_class": "is-success"
    },
    {
        "code": "legend_3_wins",
        "title": "Triple Couronne",
        "description": "Remporter la 1ère place sur 3 challenges différents. Une vraie légende.",
        "icon": "trophy",
        "category": "performance",
        "badge_class": "is-warning"
    },
    {
        "code": "veteran_5",
        "title": "Habitué du Stick",
        "description": "Participer à 5 challenges différents.",
        "icon": "heart",
        "category": "participation",
        "badge_class": "is-error"
    },
    {
        "code": "veteran_10",
        "title": "Pilier de la Salle",
        "description": "Participer à 10 challenges différents.",
        "icon": "star",
        "category": "participation",
        "badge_class": "is-primary"
    },
    {
        "code": "night_owl",
        "title": "Joueur Nocturne",
        "description": "Soumettre un high score entre minuit et 5h du matin.",
        "icon": "heart",
        "category": "secret",
        "badge_class": "is-error"
    },
    {
        "code": "konami_master",
        "title": "Code Konami",
        "description": "Avoir tapé le célèbre code secret des rétro-gamers !",
        "icon": "gem",
        "category": "secret",
        "badge_class": "is-primary"
    }
]

def seed_achievements(db: Session):
    """Seed base achievements if they don't exist yet."""
    for item in DEFAULT_ACHIEVEMENTS:
        existing = db.query(Achievement).filter(Achievement.code == item["code"]).first()
        if not existing:
            ach = Achievement(**item)
            db.add(ach)
    db.commit()

def unlock_achievement(db: Session, user_id: int, code: str) -> bool:
    """Awards an achievement to user if not already earned."""
    ach = db.query(Achievement).filter(Achievement.code == code).first()
    if not ach:
        return False

    already_unlocked = db.query(UserAchievement).filter(
        UserAchievement.user_id == user_id,
        UserAchievement.achievement_id == ach.id
    ).first()

    if already_unlocked:
        return False

    user_ach = UserAchievement(
        user_id=user_id,
        achievement_id=ach.id,
        unlocked_at=datetime.utcnow()
    )
    db.add(user_ach)
    db.commit()
    logger.info(f"Achievement unlocked: {code} for user {user_id}")
    return True

def check_submission_achievements(db: Session, user_id: int, submitted_at: datetime):
    """Checks achievements triggered by a score submission."""
    # 1. First Coin
    sub_count = db.query(ScoreSubmission).filter(ScoreSubmission.user_id == user_id).count()
    if sub_count == 1:
        unlock_achievement(db, user_id, "first_coin")

    # 2. Night Owl (between midnight and 5am)
    if 0 <= submitted_at.hour < 5:
        unlock_achievement(db, user_id, "night_owl")

def check_challenge_end_achievements(db: Session, user_id: int, rank: int):
    """Checks achievements triggered at the end of a challenge."""
    # Top 3 Podium
    if rank in (1, 2, 3):
        unlock_achievement(db, user_id, "podium_finish")
    
    # 1st place champion
    if rank == 1:
        unlock_achievement(db, user_id, "champion")

    # Check total wins (rank 1 in ChallengeResult)
    wins_count = db.query(ChallengeResult).filter(
        ChallengeResult.user_id == user_id,
        ChallengeResult.rank == 1
    ).count()
    if wins_count >= 3:
        unlock_achievement(db, user_id, "legend_3_wins")

    # Check distinct challenges participated in
    participations_count = db.query(ChallengeResult).filter(
        ChallengeResult.user_id == user_id
    ).count()
    if participations_count >= 10:
        unlock_achievement(db, user_id, "veteran_10")
    elif participations_count >= 5:
        unlock_achievement(db, user_id, "veteran_5")