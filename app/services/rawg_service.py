import logging
import re
import asyncio
from typing import List, Optional, Dict, Any
import httpx
from sqlalchemy.orm import Session
from app.config import RAWG_API_KEY
from app.models import Game

logger = logging.getLogger("rawg_service")
BASE_URL = "https://api.rawg.io/api"

def clean_html(text: Optional[str]) -> str:
    if not text:
        return ""
    clean = re.sub(r"<.*?>", "", text)
    return clean.strip()

async def search_games(query: str, page_size: int = 6) -> List[Dict[str, Any]]:
    """
    Search games on RAWG.io. Returns list of matches with covers & screenshots.
    """
    if not RAWG_API_KEY:
        logger.warning("No RAWG_API_KEY configured. Returning empty search.")
        return []

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {
                "key": RAWG_API_KEY,
                "search": query,
                "page_size": page_size,
                "search_precise": "true"
            }
            res = await client.get(f"{BASE_URL}/games", params=params)
            if res.status_code != 200:
                logger.error(f"RAWG API error: {res.status_code} - {res.text}")
                return []
            
            data = res.json()
            results = []
            for g in data.get("results", []):
                # Extract screenshots
                screenshots = [s.get("image") for s in g.get("short_screenshots", []) if s.get("image")]
                screenshot = screenshots[1] if len(screenshots) > 1 else (screenshots[0] if screenshots else g.get("background_image"))
                
                platforms = ", ".join([p.get("platform", {}).get("name", "") for p in g.get("platforms", []) if p.get("platform")])
                
                results.append({
                    "rawg_id": g.get("id"),
                    "name": g.get("name"),
                    "platform": platforms or "Arcade / Rétro",
                    "cover_image": g.get("background_image"),
                    "screenshot_image": screenshot,
                    "released": g.get("released"),
                    "rating": g.get("rating")
                })
            return results
    except Exception as e:
        logger.error(f"Failed to query RAWG API: {e}")
        return []

async def search_best_match(query: str) -> Optional[Dict[str, Any]]:
    """
    Finds the single best match for a game title on RAWG.io.
    """
    matches = await search_games(query, page_size=1)
    if matches:
        return matches[0]
    return None

async def import_games_from_list(db: Session, raw_text: str) -> Dict[str, Any]:
    """
    Parses a multiline string (from file upload or textarea),
    queries RAWG.io for each game, and inserts them into the database pool.
    """
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    
    added_count = 0
    skipped_count = 0
    rawg_found_count = 0
    results_log = []

    for line in lines:
        # Ignore comments
        if line.startswith("#") or line.startswith("//"):
            continue

        # Check if line contains a platform separator (e.g. "Game, Platform" or "Game; Platform")
        platform_hint = "Arcade / Rétro"
        if "," in line:
            parts = line.split(",", 1)
            title = parts[0].strip()
            platform_hint = parts[1].strip() or platform_hint
        elif ";" in line:
            parts = line.split(";", 1)
            title = parts[0].strip()
            platform_hint = parts[1].strip() or platform_hint
        else:
            title = line

        if not title:
            continue

        # Check if already in DB
        existing = db.query(Game).filter(Game.name.ilike(title)).first()
        if existing:
            # Ensure it's in random pool
            if not existing.in_random_pool:
                existing.in_random_pool = True
                db.commit()
            skipped_count += 1
            results_log.append({"title": title, "status": "already_exists"})
            continue

        # Search RAWG.io for details & screenshot
        rawg_match = await search_best_match(title)
        
        # Gentle rate limit delay between API queries
        if RAWG_API_KEY:
            await asyncio.sleep(0.25)

        if rawg_match:
            game_name = rawg_match["name"]
            platform = rawg_match["platform"] or platform_hint
            cover_img = rawg_match["cover_image"]
            screenshot_img = rawg_match["screenshot_image"]
            rawg_id = rawg_match["rawg_id"]
            rawg_found_count += 1
            status_text = "rawg_found"
        else:
            game_name = title
            platform = platform_hint
            cover_img = "/static/img/default-game.svg"
            screenshot_img = "/static/img/default-game.svg"
            rawg_id = None
            status_text = "fallback_created"

        new_game = Game(
            name=game_name,
            platform=platform,
            rawg_id=rawg_id,
            cover_image=cover_img,
            screenshot_image=screenshot_img,
            in_random_pool=True
        )
        db.add(new_game)
        db.commit()

        added_count += 1
        results_log.append({
            "title": game_name,
            "platform": platform,
            "status": status_text,
            "has_image": bool(rawg_match)
        })

    return {
        "total_lines": len(lines),
        "added": added_count,
        "skipped": skipped_count,
        "rawg_found": rawg_found_count,
        "details": results_log
    }

async def get_game_details(rawg_id: int) -> Optional[Dict[str, Any]]:
    """
    Get detailed info & screenshots for a specific RAWG game ID.
    """
    if not RAWG_API_KEY:
        return None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(f"{BASE_URL}/games/{rawg_id}", params={"key": RAWG_API_KEY})
            if res.status_code != 200:
                return None
            g = res.json()

            res_sc = await client.get(f"{BASE_URL}/games/{rawg_id}/screenshots", params={"key": RAWG_API_KEY})
            screenshots = []
            if res_sc.status_code == 200:
                screenshots = [s.get("image") for s in res_sc.json().get("results", []) if s.get("image")]

            screenshot = screenshots[0] if screenshots else g.get("background_image")
            platforms = ", ".join([p.get("platform", {}).get("name", "") for p in g.get("platforms", []) if p.get("platform")])

            return {
                "rawg_id": g.get("id"),
                "name": g.get("name"),
                "platform": platforms or "Arcade / Rétro",
                "cover_image": g.get("background_image"),
                "screenshot_image": screenshot,
                "description": clean_html(g.get("description")),
                "released": g.get("released")
            }
    except Exception as e:
        logger.error(f"Failed to fetch game details for {rawg_id}: {e}")
        return None