from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models import Challenge, ScoreSubmission, ChallengeResult, User
from app.config import POINTS_DISTRIBUTION, PARTICIPATION_POINTS
from app.services.achievement_service import check_challenge_end_achievements
from app.services.discord_service import notify_challenge_ended
from app.services.email_service import notify_challenge_ended_email

def get_challenge_leaderboard(db: Session, challenge_id: int) -> List[Dict[str, Any]]:
    """
    Returns unique leaderboard for a challenge.
    Only each user's best approved score is kept, sorted from highest to lowest.
    """
    submissions = (
        db.query(ScoreSubmission)
        .filter(
            ScoreSubmission.challenge_id == challenge_id,
            ScoreSubmission.status == "approved"
        )
        .order_by(desc(ScoreSubmission.score), ScoreSubmission.created_at.asc())
        .all()
    )

    seen_users = set()
    leaderboard = []

    for sub in submissions:
        if sub.user_id in seen_users:
            continue
        seen_users.add(sub.user_id)
        leaderboard.append({
            "rank": len(leaderboard) + 1,
            "user": sub.user,
            "username": sub.user.username,
            "score": sub.score,
            "screenshot_path": sub.screenshot_path,
            "comment": sub.comment,
            "submitted_at": sub.created_at,
            "submission_id": sub.id
        })

    return leaderboard

async def close_challenge_and_award_points(db: Session, challenge: Challenge, site_url: str = "") -> List[Dict[str, Any]]:
    """
    Closes the challenge, saves ChallengeResult records, credits points to users,
    triggers achievement unlocks, and sends Discord notification.
    """
    if challenge.points_awarded:
        return []

    leaderboard = get_challenge_leaderboard(db, challenge.id)
    podium_for_discord = []

    for entry in leaderboard:
        rank = entry["rank"]
        user = entry["user"]
        score = entry["score"]

        points = POINTS_DISTRIBUTION.get(rank, PARTICIPATION_POINTS)

        # Record result
        res = ChallengeResult(
            challenge_id=challenge.id,
            user_id=user.id,
            rank=rank,
            points=points,
            final_score=score
        )
        db.add(res)

        # Update user total points
        user.total_points += points

        # Check end-of-challenge achievements
        check_challenge_end_achievements(db, user.id, rank)

        podium_for_discord.append({
            "username": user.username,
            "score": score,
            "points": points,
            "rank": rank
        })

    challenge.is_closed = True
    challenge.is_active = False
    challenge.points_awarded = True
    db.commit()

    # Notifications
    game_name = challenge.game.name if challenge.game else "Jeu Rétro"
    await notify_challenge_ended(challenge.title, game_name, podium_for_discord, site_url=site_url)
    await notify_challenge_ended_email(db, challenge.title, game_name, podium_for_discord, site_url=site_url)

    return leaderboard