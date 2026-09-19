from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float
)
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    total_points = Column(Integer, default=0, index=True)
    avatar_color = Column(String(20), default="#e76e55")
    avatar_image = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    submissions = relationship("ScoreSubmission", back_populates="user", cascade="all, delete-orphan")
    results = relationship("ChallengeResult", back_populates="user")
    user_achievements = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    platform = Column(String(80), default="Arcade / NES")
    rawg_id = Column(Integer, nullable=True)
    cover_image = Column(String(500), nullable=True)
    screenshot_image = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    in_random_pool = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    challenges = relationship("Challenge", back_populates="game")

class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    rules = Column(Text, default="1 Crédit, Paramètres par défaut, Pas de triche !")
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    is_closed = Column(Boolean, default=False, index=True)
    points_awarded = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game", back_populates="challenges")
    submissions = relationship("ScoreSubmission", back_populates="challenge", cascade="all, delete-orphan")
    results = relationship("ChallengeResult", back_populates="challenge", cascade="all, delete-orphan")

class ScoreSubmission(Base):
    __tablename__ = "score_submissions"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score = Column(Integer, nullable=False, index=True)
    screenshot_path = Column(String(500), nullable=False)
    comment = Column(String(255), nullable=True)
    status = Column(String(20), default="approved")  # approved, pending, rejected
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="submissions")
    challenge = relationship("Challenge", back_populates="submissions")

class ChallengeResult(Base):
    __tablename__ = "challenge_results"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rank = Column(Integer, nullable=False)
    points = Column(Integer, nullable=False)
    final_score = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="results")
    challenge = relationship("Challenge", back_populates="results")

class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(100), nullable=False)
    description = Column(String(255), nullable=False)
    icon = Column(String(50), default="trophy")
    category = Column(String(50), default="participation") # participation, performance, secret
    badge_class = Column(String(30), default="is-primary")

    user_achievements = relationship("UserAchievement", back_populates="achievement")

class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
    unlocked_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="user_achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")