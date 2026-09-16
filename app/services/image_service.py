import os
import uuid
import logging
from pathlib import Path
from typing import Optional
from PIL import Image, ImageOps
from fastapi import UploadFile
from app.config import UPLOAD_DIR

logger = logging.getLogger("image_service")

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB

def save_score_screenshot(upload_file: UploadFile) -> Optional[str]:
    """
    Saves and optimizes a user's high score screenshot.
    Fixes smartphone EXIF rotation and converts to optimized WebP.
    Returns relative URL path e.g. '/uploads/scores/{uuid}.webp'.
    """
    try:
        filename = upload_file.filename or "score.png"
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            ext = ".png"

        # Read into Pillow
        img = Image.open(upload_file.file)

        # Fix mobile phone EXIF rotation
        img = ImageOps.exif_transpose(img)

        # Convert to RGB if needed (e.g. RGBA for WebP/JPEG)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Downscale if excessively large (e.g. > 1600px)
        max_dim = 1600
        if img.width > max_dim or img.height > max_dim:
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

        unique_name = f"{uuid.uuid4().hex}.webp"
        save_path = UPLOAD_DIR / "scores" / unique_name
        
        img.save(save_path, format="WEBP", quality=85, method=4)

        return f"/uploads/scores/{unique_name}"
    except Exception as e:
        logger.error(f"Failed to process score screenshot: {e}")
        return None

def save_game_image(upload_file: UploadFile) -> Optional[str]:
    """
    Saves an uploaded game cover/screenshot.
    """
    try:
        img = Image.open(upload_file.file)
        img = ImageOps.exif_transpose(img)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        unique_name = f"game_{uuid.uuid4().hex}.webp"
        save_path = UPLOAD_DIR / "games" / unique_name
        img.save(save_path, format="WEBP", quality=85)
        return f"/uploads/games/{unique_name}"
    except Exception as e:
        logger.error(f"Failed to process game image: {e}")
        return None