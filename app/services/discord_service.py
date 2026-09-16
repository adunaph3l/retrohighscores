import logging
from typing import List, Optional
import httpx
from app.config import DISCORD_WEBHOOK_URL

logger = logging.getLogger("discord_service")

async def send_discord_webhook(payload: dict) -> bool:
    if not DISCORD_WEBHOOK_URL:
        logger.info("No DISCORD_WEBHOOK_URL configured. Skipping notification.")
        return False
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(DISCORD_WEBHOOK_URL, json=payload)
            if response.status_code in (200, 204):
                logger.info("Discord notification sent successfully.")
                return True
            else:
                logger.error(f"Discord webhook failed: {response.status_code} - {response.text}")
                return False
    except Exception as e:
        logger.error(f"Error sending Discord webhook: {e}")
        return False

async def notify_challenge_started(
    challenge_title: str,
    game_name: str,
    platform: str,
    rules: str,
    end_date_str: str,
    image_url: Optional[str] = None,
    site_url: Optional[str] = None
):
    embed = {
        "title": f"🕹️ NOUVEAU CHALLENGE : {game_name}",
        "description": f"**{challenge_title}**\n\nUn nouveau challenge vient de commencer ! Sortez vos sticks d'arcade et vos manettes !",
        "color": 0xf7d51d,  # Retro Yellow
        "fields": [
            {"name": "🎮 Jeu", "value": game_name, "inline": True},
            {"name": "📟 Plateforme", "value": platform or "Arcade / NES", "inline": True},
            {"name": "⏳ Date limite", "value": end_date_str, "inline": False},
            {"name": "📜 Règles", "value": rules or "1 Crédit, Paramètres d'usine", "inline": False},
        ],
        "footer": {"text": "Retro High Scores • Insérez une pièce pour participer !"}
    }

    if image_url and image_url.startswith("http"):
        embed["image"] = {"url": image_url}

    if site_url:
        embed["url"] = site_url

    payload = {
        "username": "Retro Highscores Bot",
        "avatar_url": "https://nostalgic-css.github.io/NES.css/favicon.png",
        "content": "📢 **UN NOUVEAU DÉFI ARCADE EST EN LIGNE !** @everyone",
        "embeds": [embed]
    }
    return await send_discord_webhook(payload)

async def notify_score_submitted(
    username: str,
    game_name: str,
    score: int,
    rank: int,
    screenshot_url: Optional[str] = None,
    site_url: Optional[str] = None
):
    rank_icon = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
    score_formatted = f"{score:,}".replace(",", " ")
    embed = {
        "title": f"🔥 NOUVEAU SCORE PAR {username.upper()} !",
        "description": f"**{username}** vient d'enregistrer un score sur **{game_name}** !",
        "color": 0x92cc41,  # Retro Green
        "fields": [
            {"name": "🕹️ Jeu", "value": game_name, "inline": True},
            {"name": "🎯 Score", "value": score_formatted, "inline": True},
            {"name": "🏅 Rang actuel", "value": f"{rank_icon} ({rank}e position)", "inline": True},
        ],
        "footer": {"text": "Retro High Scores • Qui osera faire mieux ?"}
    }

    if screenshot_url and screenshot_url.startswith("http"):
        embed["image"] = {"url": screenshot_url}

    if site_url:
        embed["url"] = site_url

    payload = {
        "username": "Retro Highscores Bot",
        "avatar_url": "https://nostalgic-css.github.io/NES.css/favicon.png",
        "content": f"⚡ Nouveau score enregistré sur **{game_name}** !",
        "embeds": [embed]
    }
    return await send_discord_webhook(payload)

async def notify_challenge_ended(
    challenge_title: str,
    game_name: str,
    podium: List[dict],
    site_url: Optional[str] = None
):
    embed = {
        "title": f"🏁 CHALLENGE TERMINÉ : {game_name}",
        "description": f"Le challenge **{challenge_title}** est officiellement clos ! Félicitations à tous les participants !",
        "color": 0xe76e55,  # Retro Red
        "fields": [],
        "footer": {"text": "Retro High Scores • Les points ont été distribués pour le Hall of Fame !"}
    }

    medals = ["🥇 1ère place", "🥈 2ème place", "🥉 3ème place"]
    if podium:
        for idx, entry in enumerate(podium[:3]):
            score_formatted = f"{entry['score']:,}".replace(",", " ")
            embed["fields"].append({
                "name": f"{medals[idx]} : {entry['username']}",
                "value": f"Score: **{score_formatted}** (+{entry['points']} pts)",
                "inline": False
            })
    else:
        embed["fields"].append({
            "name": "Aucun score",
            "value": "Personne n'a soumis de score pour ce challenge !",
            "inline": False
        })

    if site_url:
        embed["url"] = site_url

    payload = {
        "username": "Retro Highscores Bot",
        "avatar_url": "https://nostalgic-css.github.io/NES.css/favicon.png",
        "content": f"🎉 **RÉSULTATS DU CHALLENGE SUR {game_name.upper()} !**",
        "embeds": [embed]
    }
    return await send_discord_webhook(payload)

async def test_discord_webhook() -> bool:
    payload = {
        "username": "Retro Highscores Bot",
        "avatar_url": "https://nostalgic-css.github.io/NES.css/favicon.png",
        "content": "👾 **Bip bop ! Test du Webhook Discord réussi avec succès !** La liaison avec la salle d'arcade fonctionne parfaitement !"
    }
    return await send_discord_webhook(payload)