import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models import EmailSetting, User

logger = logging.getLogger("email_service")

def get_email_settings(db: Session) -> EmailSetting:
    """Retrieves existing EmailSetting or initializes a default row."""
    settings = db.query(EmailSetting).first()
    if not settings:
        settings = EmailSetting(
            smtp_host="",
            smtp_port=587,
            smtp_user="",
            smtp_password="",
            smtp_from_email="",
            smtp_from_name="Retro High Scores",
            smtp_use_tls=True,
            smtp_use_ssl=False,
            enabled=False,
            notify_challenge_started=True,
            notify_score_submitted=True,
            notify_challenge_ended=True
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

def get_all_player_emails(db: Session) -> List[str]:
    """Retrieves all registered player email addresses."""
    users = db.query(User).filter(User.email.isnot(None)).all()
    emails = []
    for u in users:
        cleaned = (u.email or "").strip()
        if cleaned and "@" in cleaned and cleaned not in emails:
            emails.append(cleaned)
    return emails

def _send_email_sync(
    settings: EmailSetting,
    to_emails: List[str],
    subject: str,
    html_content: str,
    text_content: str = ""
) -> Tuple[bool, str]:
    """Synchronously dispatches an email via SMTP."""
    if not settings.smtp_host or not settings.smtp_port:
        return False, "Serveur SMTP non configuré (Hôte ou port manquant)."

    from_email = settings.smtp_from_email or settings.smtp_user or "noreply@retrohighscores.local"
    from_name = settings.smtp_from_name or "Retro High Scores"

    if not to_emails:
        return False, "Aucune adresse email destinataire fournie."

    try:
        # Create MIME message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = formataddr((from_name, from_email))
        # If multiple recipients, use Bcc so players cannot see each other's emails
        if len(to_emails) == 1:
            msg["To"] = to_emails[0]
        else:
            msg["To"] = from_email

        if not text_content:
            text_content = "Veuillez activer l'affichage HTML pour lire ce message rétro."

        part_text = MIMEText(text_content, "plain", "utf-8")
        part_html = MIMEText(html_content, "html", "utf-8")
        msg.attach(part_text)
        msg.attach(part_html)

        # Connection
        if settings.smtp_use_ssl:
            server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=12)
        else:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=12)

        server.ehlo()
        if settings.smtp_use_tls and not settings.smtp_use_ssl:
            server.starttls()
            server.ehlo()

        if settings.smtp_user and settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)

        server.sendmail(from_email, to_emails, msg.as_string())
        server.quit()

        logger.info(f"Email sent successfully to {len(to_emails)} recipient(s): '{subject}'")
        return True, "Email envoyé avec succès !"
    except Exception as e:
        logger.error(f"SMTP error while sending email: {e}", exc_info=True)
        return False, f"Erreur SMTP: {str(e)}"

async def send_email_async(
    settings: EmailSetting,
    to_emails: List[str],
    subject: str,
    html_content: str,
    text_content: str = ""
) -> Tuple[bool, str]:
    """Asynchronously dispatches an email in a thread."""
    return await asyncio.to_thread(
        _send_email_sync, settings, to_emails, subject, html_content, text_content
    )

def _build_retro_email_wrapper(title: str, subtitle: str, content_html: str, action_url: Optional[str] = None, action_text: str = "ACCÉDER À LA BORNE") -> str:
    """Builds a complete, responsive retro 8-bit HTML email wrapper."""
    action_button_html = ""
    if action_url:
        action_button_html = f"""
        <div style="text-align: center; margin: 30px 0 20px 0;">
            <a href="{action_url}" target="_blank" style="display: inline-block; background-color: #92cc41; color: #000000; font-family: 'Courier New', Courier, monospace; font-size: 14px; font-weight: bold; text-decoration: none; padding: 14px 28px; border: 3px solid #ffffff; box-shadow: 4px 4px 0px #000000; text-transform: uppercase; letter-spacing: 1px;">
                ▶ {action_text}
            </a>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #15181d; font-family: 'Press Start 2P', 'Courier New', Courier, monospace; color: #ffffff; -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%;">
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #15181d; padding: 25px 10px;">
        <tr>
            <td align="center">
                <!-- Container principal rétro -->
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #212529; border: 4px solid #ffffff; box-shadow: 6px 6px 0px #000000;">
                    
                    <!-- Header Rétro Arcade -->
                    <tr>
                        <td style="background-color: #000000; padding: 20px; text-align: center; border-bottom: 4px solid #ffffff;">
                            <div style="font-size: 18px; color: #f7d51d; font-weight: bold; letter-spacing: 2px; margin-bottom: 6px;">
                                🕹️ RETRO HIGH SCORES
                            </div>
                            <div style="font-size: 10px; color: #209cee; letter-spacing: 1px; text-transform: uppercase;">
                                {subtitle}
                            </div>
                        </td>
                    </tr>

                    <!-- Bannière Titre -->
                    <tr>
                        <td style="padding: 25px 25px 10px 25px;">
                            <h2 style="margin: 0 0 15px 0; color: #f7d51d; font-size: 15px; text-align: center; line-height: 1.4;">
                                {title}
                            </h2>
                        </td>
                    </tr>

                    <!-- Contenu du Message -->
                    <tr>
                        <td style="padding: 10px 25px 20px 25px; font-size: 12px; line-height: 1.6; color: #f0f0f0;">
                            {content_html}
                            {action_button_html}
                        </td>
                    </tr>

                    <!-- Footer Rétro -->
                    <tr>
                        <td style="background-color: #1a1c23; padding: 18px; text-align: center; border-top: 3px solid #3d414d; font-size: 9px; color: #888888; line-height: 1.5;">
                            👾 <strong>Retro High Scores</strong> • Salle d'arcade &amp; Challenges rétro<br>
                            <span style="color: #666666;">Insérez une pièce pour continuer • Notification officielle automatique</span>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

async def send_test_email(db: Session, target_email: str, site_url: str = "") -> Tuple[bool, str]:
    """Sends a retro test email to confirm SMTP connectivity."""
    settings = get_email_settings(db)
    subject = "👾 [TEST] Liaison Arcade Réussie ! - Retro High Scores"
    
    content_html = f"""
    <div style="background-color: #2b2e38; border: 2px solid #92cc41; padding: 15px; margin-bottom: 20px; text-align: center;">
        <span style="font-size: 24px;">✨</span><br>
        <strong style="color: #92cc41; font-size: 13px;">TEST DE CONNEXION SMTP RÉUSSI !</strong>
    </div>

    <p style="margin-bottom: 12px;">
        Bravo administrateur ! Votre serveur de messagerie SMTP est parfaitement configuré et communique sans accroc avec votre plateforme <strong>Retro High Scores</strong>.
    </p>

    <div style="background-color: #1a1c23; border: 2px solid #ffffff; padding: 12px; margin: 15px 0; font-size: 11px;">
        <p style="margin: 4px 0;"><strong>Hôte SMTP :</strong> <span style="color: #209cee;">{settings.smtp_host}</span></p>
        <p style="margin: 4px 0;"><strong>Port :</strong> <span style="color: #f7d51d;">{settings.smtp_port}</span></p>
        <p style="margin: 4px 0;"><strong>Sécurité :</strong> <span style="color: #92cc41;">{'SSL' if settings.smtp_use_ssl else ('STARTTLS' if settings.smtp_use_tls else 'Aucune')}</span></p>
        <p style="margin: 4px 0;"><strong>Expéditeur :</strong> <span style="color: #e76e55;">{settings.smtp_from_email or settings.smtp_user}</span></p>
    </div>

    <p style="margin-bottom: 5px; font-size: 11px; color: #aaaaaa;">
        Vos joueurs recevront désormais automatiquement les alertes lors des lancements de défis, des nouveaux high scores et des fins de challenges !
    </p>
    """

    html = _build_retro_email_wrapper(
        title="🔔 Bip Bop ! Test de Notification",
        subtitle="CONFIGURATION DU SERVEUR DE COURRIEL",
        content_html=content_html,
        action_url=site_url or "http://localhost:8080",
        action_text="RETOURNER À L'ADMINISTRATION"
    )

    return await send_email_async(
        settings=settings,
        to_emails=[target_email],
        subject=subject,
        html_content=html,
        text_content="Bip bop ! Test SMTP réussi avec succès sur Retro High Scores !"
    )

async def notify_challenge_started_email(
    db: Session,
    challenge_title: str,
    game_name: str,
    platform: str,
    rules: str,
    end_date_str: str,
    image_url: Optional[str] = None,
    site_url: Optional[str] = None
) -> Tuple[bool, str]:
    """Broadcasts an email to all players when a new challenge is launched."""
    settings = get_email_settings(db)
    if not settings.enabled or not settings.notify_challenge_started:
        logger.info("Email notifications for challenge start disabled.")
        return False, "Notifications email désactivées."

    recipients = get_all_player_emails(db)
    if not recipients:
        logger.info("No registered players with emails to notify.")
        return False, "Aucun joueur inscrit avec une adresse email."

    subject = f"🕹️ NOUVEAU DÉFI ARCADE : {game_name.upper()} !"

    image_block = ""
    if image_url and image_url.startswith("http"):
        image_block = f"""
        <div style="text-align: center; margin: 15px 0;">
            <img src="{image_url}" alt="{game_name}" style="max-width: 100%; height: auto; max-height: 220px; border: 3px solid #ffffff; box-shadow: 4px 4px 0px #000000;">
        </div>
        """

    content_html = f"""
    <div style="background-color: #2b2e38; border: 2px solid #f7d51d; padding: 15px; margin-bottom: 15px; text-align: center;">
        <span style="font-size: 20px;">🔥</span><br>
        <strong style="color: #f7d51d; font-size: 13px;">UN NOUVEAU CHALLENGE COMMENCE !</strong><br>
        <span style="font-size: 11px; color: #ffffff;">{challenge_title}</span>
    </div>

    {image_block}

    <div style="background-color: #1a1c23; border: 2px solid #ffffff; padding: 14px; margin: 15px 0; font-size: 11px;">
        <p style="margin: 6px 0;">🎮 <strong>Jeu :</strong> <span style="color: #f7d51d; font-weight: bold;">{game_name}</span></p>
        <p style="margin: 6px 0;">📟 <strong>Plateforme :</strong> <span style="color: #209cee;">{platform or 'Arcade / Rétro'}</span></p>
        <p style="margin: 6px 0;">⏳ <strong>Date limite :</strong> <span style="color: #92cc41; font-weight: bold;">{end_date_str}</span></p>
        <p style="margin: 6px 0;">📜 <strong>Règles :</strong> <span style="color: #ffffff;">{rules or '1 Crédit, Paramètres par défaut'}</span></p>
    </div>

    <p style="text-align: center; margin-top: 15px; font-size: 11px;">
        Faites chauffer la borne d'arcade et inscrivez votre nom sur le tableau des scores avant la clôture !
    </p>
    """

    html = _build_retro_email_wrapper(
        title=f"🕹️ DÉFI OUVERT : {game_name}",
        subtitle="NOUVEAU CHALLENGE OFFICIEL",
        content_html=content_html,
        action_url=site_url,
        action_text="INSCRIRE MON HIGH SCORE"
    )

    return await send_email_async(
        settings=settings,
        to_emails=recipients,
        subject=subject,
        html_content=html,
        text_content=f"Nouveau challenge sur {game_name} ! Connectez-vous sur {site_url or ''} pour participer."
    )

async def notify_score_submitted_email(
    db: Session,
    username: str,
    game_name: str,
    score: int,
    rank: int,
    screenshot_url: Optional[str] = None,
    site_url: Optional[str] = None
) -> Tuple[bool, str]:
    """Broadcasts an email to all players when a new score is recorded."""
    settings = get_email_settings(db)
    if not settings.enabled or not settings.notify_score_submitted:
        return False, "Notifications email pour nouveaux scores désactivées."

    recipients = get_all_player_emails(db)
    if not recipients:
        return False, "Aucun destinataire email."

    rank_icon = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
    score_formatted = f"{score:,}".replace(",", " ")

    subject = f"⚡ {username.upper()} marque {score_formatted} pts sur {game_name} !"

    image_block = ""
    if screenshot_url and screenshot_url.startswith("http"):
        image_block = f"""
        <div style="text-align: center; margin: 15px 0;">
            <p style="font-size: 9px; color: #f7d51d; margin-bottom: 6px;">📸 Capture d'écran de preuve :</p>
            <img src="{screenshot_url}" alt="Preuve de score" style="max-width: 100%; height: auto; max-height: 220px; border: 3px solid #ffffff; box-shadow: 4px 4px 0px #000000;">
        </div>
        """

    content_html = f"""
    <div style="background-color: #2b2e38; border: 2px solid #209cee; padding: 15px; margin-bottom: 15px; text-align: center;">
        <span style="font-size: 20px;">💥</span><br>
        <strong style="color: #209cee; font-size: 13px;">NOUVEAU HIGH SCORE ENREGISTRÉ !</strong>
    </div>

    <div style="background-color: #1a1c23; border: 2px solid #ffffff; padding: 14px; margin: 15px 0; font-size: 11px;">
        <p style="margin: 6px 0;">👤 <strong>Joueur :</strong> <span style="color: #209cee; font-weight: bold;">{username}</span></p>
        <p style="margin: 6px 0;">🕹️ <strong>Jeu :</strong> <span style="color: #ffffff;">{game_name}</span></p>
        <p style="margin: 6px 0;">🎯 <strong>Score :</strong> <span style="color: #f7d51d; font-weight: bold; font-size: 13px;">{score_formatted} PTS</span></p>
        <p style="margin: 6px 0;">🏅 <strong>Position actuelle :</strong> <span style="color: #92cc41; font-weight: bold;">{rank_icon} ({rank}e position)</span></p>
    </div>

    {image_block}

    <p style="text-align: center; margin-top: 15px; font-size: 11px;">
        Allez-vous laisser <strong>{username}</strong> dominer la salle d'arcade ? Rendez-vous sur la borne !
    </p>
    """

    html = _build_retro_email_wrapper(
        title=f"⚡ RECORD : {score_formatted} PTS",
        subtitle=f"NOUVEAU SCORE PAR {username.upper()}",
        content_html=content_html,
        action_url=site_url,
        action_text="BATTER CE SCORE MAINTENANT"
    )

    return await send_email_async(
        settings=settings,
        to_emails=recipients,
        subject=subject,
        html_content=html,
        text_content=f"{username} a réalisé {score_formatted} pts sur {game_name} (rang {rank}) ! Voir sur {site_url or ''}"
    )

async def notify_challenge_ended_email(
    db: Session,
    challenge_title: str,
    game_name: str,
    podium: List[dict],
    site_url: Optional[str] = None
) -> Tuple[bool, str]:
    """Broadcasts an email to all players when a challenge closes with final results."""
    settings = get_email_settings(db)
    if not settings.enabled or not settings.notify_challenge_ended:
        return False, "Notifications email de clôture désactivées."

    recipients = get_all_player_emails(db)
    if not recipients:
        return False, "Aucun destinataire email."

    subject = f"🏁 PODIUM FINAL : Résultats du défi {game_name.upper()} !"

    podium_rows = ""
    medals = ["🥇 1ère place", "🥈 2ème place", "🥉 3ème place"]
    colors = ["#f7d51d", "#ffffff", "#e76e55"]

    if podium:
        for idx, entry in enumerate(podium[:3]):
            score_formatted = f"{entry['score']:,}".replace(",", " ")
            podium_rows += f"""
            <tr style="border-bottom: 1px dashed #3d414d;">
                <td style="padding: 10px; color: {colors[idx]}; font-weight: bold;">{medals[idx]}</td>
                <td style="padding: 10px; color: #209cee; font-weight: bold;">{entry['username']}</td>
                <td style="padding: 10px; text-align: right; color: #f7d51d;">{score_formatted} pts</td>
                <td style="padding: 10px; text-align: right; color: #92cc41;">+{entry['points']} pts</td>
            </tr>
            """
    else:
        podium_rows = """
        <tr>
            <td colspan="4" style="padding: 15px; text-align: center; color: #888888;">
                Aucun score n'a été enregistré pour ce challenge !
            </td>
        </tr>
        """

    content_html = f"""
    <div style="background-color: #2b2e38; border: 2px solid #e76e55; padding: 15px; margin-bottom: 15px; text-align: center;">
        <span style="font-size: 20px;">🏁</span><br>
        <strong style="color: #e76e55; font-size: 13px;">CHALLENGE OFFICIELLEMENT CLÔTURÉ !</strong><br>
        <span style="font-size: 11px; color: #ffffff;">{challenge_title} ({game_name})</span>
    </div>

    <p style="margin-bottom: 12px; font-size: 11px; text-align: center;">
        Les points ont été distribués pour le <strong>Hall of Fame</strong> ! Voici les maîtres de la borne :
    </p>

    <div style="background-color: #1a1c23; border: 2px solid #ffffff; padding: 10px; margin: 15px 0;">
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="font-size: 10px;">
            <thead>
                <tr style="border-bottom: 2px solid #ffffff; color: #f7d51d;">
                    <th style="padding: 8px; text-align: left;">Rang</th>
                    <th style="padding: 8px; text-align: left;">Joueur</th>
                    <th style="padding: 8px; text-align: right;">Score</th>
                    <th style="padding: 8px; text-align: right;">Gain</th>
                </tr>
            </thead>
            <tbody>
                {podium_rows}
            </tbody>
        </table>
    </div>

    <p style="text-align: center; margin-top: 15px; font-size: 11px;">
        Félicitations à tous les combattants du joystick ! Consultez le classement général mis à jour.
    </p>
    """

    html = _build_retro_email_wrapper(
        title=f"🏁 PODIUM ARCADE : {game_name}",
        subtitle="RÉSULTATS DU CHALLENGE & POINTS",
        content_html=content_html,
        action_url=site_url,
        action_text="VOIR LE HALL OF FAME"
    )

    return await send_email_async(
        settings=settings,
        to_emails=recipients,
        subject=subject,
        html_content=html,
        text_content=f"Le challenge sur {game_name} est terminé ! Félicitations aux vainqueurs."
    )
