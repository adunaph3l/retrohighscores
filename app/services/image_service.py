import os
import uuid
import logging
from pathlib import Path
from typing import Optional
from PIL import Image, ImageOps
from fastapi import UploadFile
from app.config import UPLOAD_DIR

logger = logging.getLogger("image_service")

# Register pillow-heif opener for Apple iPhone HEIC/HEIF photos
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    logger.info("pillow_heif registered successfully: HEIC/HEIF support active.")
except ImportError:
    logger.warning("pillow_heif is not installed. HEIC images might fail to process.")

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic", ".heif"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB

def save_score_screenshot(upload_file: UploadFile) -> Optional[str]:
    """
    Saves and optimizes a user's high score screenshot.
    Supports standard formats (JPG, PNG, WebP) and Apple iPhone HEIC/HEIF.
    Fixes smartphone EXIF rotation and converts to universal, optimized WebP.
    Returns relative URL path e.g. '/uploads/scores/{uuid}.webp'.
    """
    try:
        filename = upload_file.filename or "score.png"
        ext = os.path.splitext(filename)[1].lower()
        content_type = (upload_file.content_type or "").lower()

        is_heic = ext in {".heic", ".heif"} or "heic" in content_type or "heif" in content_type

        # Verify extension is permitted
        if ext not in ALLOWED_EXTENSIONS and not is_heic:
            logger.warning(f"Rejected unapproved image format: {filename} (type: {content_type})")
            return None

        # Reset file stream position
        upload_file.file.seek(0)

        # Open image with Pillow (pillow_heif handles HEIC automatically)
        img = Image.open(upload_file.file)

        # Fix mobile phone EXIF rotation (ensures photos are right-side up)
        img = ImageOps.exif_transpose(img)

        # Convert to RGB (handles RGBA, P, CMYK, and Apple 10-bit HDR HEIC modes)
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Downscale if excessively large (e.g. > 1600px)
        max_dim = 1600
        if img.width > max_dim or img.height > max_dim:
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

        unique_name = f"{uuid.uuid4().hex}.webp"
        save_path = UPLOAD_DIR / "scores" / unique_name
        
        # Save as standard WebP (viewable on all desktop and mobile browsers)
        img.save(save_path, format="WEBP", quality=85, method=4)

        logger.info(f"Successfully processed and converted screenshot ({filename}) to {save_path.name}")
        return f"/uploads/scores/{unique_name}"
    except Exception as e:
        logger.error(f"Failed to process score screenshot ({upload_file.filename}): {e}")
        return None

def save_game_image(upload_file: UploadFile) -> Optional[str]:
    """
    Saves an uploaded game cover/screenshot.
    """
    try:
        upload_file.file.seek(0)
        img = Image.open(upload_file.file)
        img = ImageOps.exif_transpose(img)
        if img.mode != "RGB":
            img = img.convert("RGB")

        unique_name = f"game_{uuid.uuid4().hex}.webp"
        save_path = UPLOAD_DIR / "games" / unique_name
        img.save(save_path, format="WEBP", quality=85)
        return f"/uploads/games/{unique_name}"
    except Exception as e:
        logger.error(f"Failed to process game image: {e}")
        return None