# models.py
from flask_sqlalchemy import SQLAlchemy
import secrets
import string
import datetime
import pytz  # <--- NEW

db = SQLAlchemy()

# -------------------- Helpers --------------------
def generate_game_id(length=24):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

def generate_player_id(length=10):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

def generate_match_id(length=32):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

# Always use Jakarta timezone (GMT+7)
JAKARTA_TZ = pytz.timezone("Asia/Jakarta")

def now_jakarta():
    """Return current time in Asia/Jakarta tz."""
    return datetime.datetime.now(JAKARTA_TZ)

# -------------------- Models --------------------
class GameInfo(db.Model):
    __tablename__ = "gameinfo"

    game_id = db.Column(db.String(24), primary_key=True, default=generate_game_id)
    game_name = db.Column(db.String(255), nullable=False)
    game_place = db.Column(db.String(255), nullable=False)
    host_email = db.Column(db.String(255), nullable=False)

    created_at = db.Column(db.DateTime, default=now_jakarta)   # <- TZ aware
    game_end_at = db.Column(db.DateTime, nullable=True)
    event_duration = db.Column(db.String(20), nullable=True)  # "HH:MM:SS"

    players = db.relationship("Player", backref="game", cascade="all, delete-orphan")
    playground = db.relationship("Playground", backref="game", uselist=False, cascade="all, delete-orphan")
    game_details = db.relationship("GameDetail", backref="game", cascade="all, delete-orphan")

    def end_game(self):
        """Mark game as ended, set game_end_at and duration"""
        self.game_end_at = now_jakarta()
        if self.created_at:
            delta = self.game_end_at - self.created_at
            self.event_duration = str(delta).split(".")[0]
        else:
            self.event_duration = None


class Playground(db.Model):
    __tablename__ = "playground"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    game_id = db.Column(db.String(24), db.ForeignKey("gameinfo.game_id"), nullable=False)

    sport = db.Column(db.String(50), nullable=False)
    game_type = db.Column(db.String(50), nullable=False)
    game_format = db.Column(db.String(50), nullable=False)
    point_limit = db.Column(db.Integer, nullable=False)
    courts_count = db.Column(db.Integer, nullable=False)


class Player(db.Model):
    __tablename__ = "players"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    player_code = db.Column(db.String(10), nullable=False)
    player_id = db.Column(db.String(10), nullable=False, default=generate_player_id, unique=True)
    player_name = db.Column(db.String(255), nullable=False)
    game_id = db.Column(db.String(24), db.ForeignKey("gameinfo.game_id"), nullable=False)

    @staticmethod
    def create_with_code(idx, name, game_id):
        return Player(
            player_code=f"P-{idx:02}",
            player_name=name,
            game_id=game_id
        )


class GameDetail(db.Model):
    __tablename__ = "game_details"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    game_no = db.Column(db.Integer, nullable=False)
    match_id = db.Column(db.String(32), nullable=False, default=generate_match_id)
    game_id = db.Column(db.String(24), db.ForeignKey("gameinfo.game_id"), nullable=False)

    court_no = db.Column(db.String(20), nullable=False)
    team_a_players = db.Column(db.String(255), nullable=True)  # e.g. "Dimas,Kenny"
    team_b_players = db.Column(db.String(255), nullable=True)  # e.g. "Ryan,Amin"

    score_a = db.Column(db.Integer, default=0)   # 👈 NEW
    score_b = db.Column(db.Integer, default=0)   # 👈 NEW

    winner_flag = db.Column(db.String(1), nullable=True)

    match_start_at = db.Column(db.DateTime, default=now_jakarta)
    match_end_at = db.Column(db.DateTime, nullable=True)
    match_duration = db.Column(db.String(20), nullable=True)

    def end_match(self):
        self.match_end_at = now_jakarta()
        if self.match_start_at:
            delta = self.match_end_at - self.match_start_at
            self.match_duration = str(delta).split(".")[0]
        else:
            self.match_duration = None

