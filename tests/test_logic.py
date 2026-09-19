import unittest
from datetime import datetime

class TestLogic(unittest.TestCase):
    def test_points_distribution(self):
        points_map = {1: 100, 2: 75, 3: 50, 4: 35, 5: 25, 6: 15, 7: 15, 8: 15, 9: 15, 10: 15}
        participation = 10

        self.assertEqual(points_map.get(1, participation), 100)
        self.assertEqual(points_map.get(2, participation), 75)
        self.assertEqual(points_map.get(3, participation), 50)
        self.assertEqual(points_map.get(4, participation), 35)
        self.assertEqual(points_map.get(5, participation), 25)
        self.assertEqual(points_map.get(6, participation), 15)
        self.assertEqual(points_map.get(10, participation), 15)
        self.assertEqual(points_map.get(11, participation), 10)
        self.assertEqual(points_map.get(99, participation), 10)

    def test_score_tiebreaker_and_uniqueness(self):
        # Sample raw submissions: (user_id, score, created_at)
        raw_submissions = [
            {"user_id": 1, "score": 50000, "time": datetime(2026, 9, 1, 10, 0)},
            {"user_id": 2, "score": 75000, "time": datetime(2026, 9, 1, 12, 0)},
            {"user_id": 1, "score": 90000, "time": datetime(2026, 9, 2, 14, 0)}, # User 1 updated score
            {"user_id": 3, "score": 75000, "time": datetime(2026, 9, 1, 11, 0)}, # Earlier than user 2
        ]

        # Sort: score desc, time asc
        sorted_subs = sorted(raw_submissions, key=lambda x: (-x["score"], x["time"]))

        seen_users = set()
        leaderboard = []
        for s in sorted_subs:
            if s["user_id"] in seen_users:
                continue
            seen_users.add(s["user_id"])
            leaderboard.append(s)

        # Expected:
        # Rank 1: user 1 with 90000
        # Rank 2: user 3 with 75000 (at 11:00)
        # Rank 3: user 2 with 75000 (at 12:00)
        self.assertEqual(leaderboard[0]["user_id"], 1)
        self.assertEqual(leaderboard[0]["score"], 90000)
        self.assertEqual(leaderboard[1]["user_id"], 3)
        self.assertEqual(leaderboard[2]["user_id"], 2)
        self.assertEqual(len(leaderboard), 3)

    def test_discord_formatting(self):
        score = 1250450
        formatted = f"{score:,}".replace(",", " ")
        self.assertEqual(formatted, "1 250 450")

    def test_html_cleaner(self):
        import re
        html = "<p>Super <strong>arcade</strong> game &amp; adventure!</p>"
        clean = re.sub(r"<.*?>", "", html).strip()
        self.assertEqual(clean, "Super arcade game &amp; adventure!")

    def test_line_parsing(self):
        sample = """
        # Ceci est un commentaire
        Pac-Man
        Galaga, Arcade
        Sonic The Hedgehog; Mega Drive
        // Autre commentaire
        
        Metal Slug
        """
        lines = [l.strip() for l in sample.splitlines() if l.strip()]
        parsed = []
        for line in lines:
            if line.startswith("#") or line.startswith("//"):
                continue
            if "," in line:
                parts = line.split(",", 1)
                title, platform = parts[0].strip(), parts[1].strip()
            elif ";" in line:
                parts = line.split(";", 1)
                title, platform = parts[0].strip(), parts[1].strip()
            else:
                title, platform = line, "Arcade / Rétro"
            parsed.append((title, platform))

        self.assertEqual(len(parsed), 4)
        self.assertEqual(parsed[0], ("Pac-Man", "Arcade / Rétro"))
        self.assertEqual(parsed[1], ("Galaga", "Arcade"))
        self.assertEqual(parsed[2], ("Sonic The Hedgehog", "Mega Drive"))
        self.assertEqual(parsed[3], ("Metal Slug", "Arcade / Rétro"))

    def test_heic_allowed(self):
        allowed = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic", ".heif"}
        self.assertIn(".heic", allowed)
        self.assertIn(".heif", allowed)
        self.assertTrue("photo.HEIC".lower().endswith(tuple(allowed)))

    def test_secret_achievements_structure(self):
        import sys
        from unittest.mock import MagicMock
        for mod in ['sqlalchemy', 'sqlalchemy.orm', 'sqlalchemy.ext.declarative', 'fastapi', 'httpx', 'dotenv', 'pydantic']:
            if mod not in sys.modules:
                sys.modules[mod] = MagicMock()
        from app.services.achievement_service import DEFAULT_ACHIEVEMENTS
        
        secret_achievements = [a for a in DEFAULT_ACHIEVEMENTS if a.get("category") == "secret"]
        self.assertGreaterEqual(len(secret_achievements), 5)
        
        secret_codes = {a["code"] for a in secret_achievements}
        self.assertIn("lucky_number", secret_codes)
        self.assertIn("sunday_warrior", secret_codes)
        self.assertIn("speedy_challenger", secret_codes)
        self.assertIn("crt_master", secret_codes)
        self.assertIn("custom_avatar", secret_codes)

    def test_lucky_number_condition(self):
        score_lucky = 77700
        self.assertTrue("777" in str(score_lucky) or "42" in str(score_lucky) or "1337" in str(score_lucky))
        score_normal = 12345
        self.assertFalse("777" in str(score_normal) or "42" in str(score_normal) or "1337" in str(score_normal))

if __name__ == "__main__":
    unittest.main()