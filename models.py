# models.py
from flask_sqlalchemy import SQLAlchemy
import secrets
import string
import datetime
import pytz

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

JAKARTA_TZ = pytz.timezone("Asia/Jakarta")

def now_jakarta():
    """Return current time in Asia/Jakarta tz (naive for DB)."""
    return datetime.datetime.now(JAKARTA_TZ).replace(tzinfo=None)

def convert_court_number_to_letter(n: int) -> str:
    """Convert 1,2,3 → A,B,C"""
    return chr(64 + n) if 1 <= n <= 26 else str(n)


# -------------------- Models --------------------
class GameInfo(db.Model):
    __tablename__ = "gameinfo"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    game_id = db.Column(db.String(24), unique=True, default=generate_game_id)
    game_name = db.Column(db.String(255), nullable=False)
    game_place = db.Column(db.String(255), nullable=False)
    host_email = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=now_jakarta)

    playground = db.relationship("Playground", backref="game", uselist=False, cascade="all, delete-orphan")
    players = db.relationship("Player", backref="game", cascade="all, delete-orphan")
    drawings = db.relationship("Drawing", backref="game", cascade="all, delete-orphan")


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
    player_code = db.Column(db.String(10), nullable=False)  # e.g. P-01
    player_id = db.Column(db.String(10), nullable=False, unique=True, default=generate_player_id)
    player_name = db.Column(db.String(255), nullable=False)
    game_id = db.Column(db.String(24), db.ForeignKey("gameinfo.game_id"), nullable=False)


class Drawing(db.Model):
    __tablename__ = "drawing"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    game_id = db.Column(db.String(24), db.ForeignKey("gameinfo.game_id"), nullable=False)

    game_no = db.Column(db.Integer, nullable=False)
    court_no = db.Column(db.String(5), nullable=False)  # "A", "B", "C"
    team_side = db.Column(db.String(5), nullable=False)  # "A" or "B"

    player_code = db.Column(db.String(10), nullable=False)
    player_id = db.Column(db.String(10), nullable=False)
    player_match_number = db.Column(db.Integer, nullable=False)

    match_id = db.Column(db.String(32), nullable=False, default=generate_match_id)
    match_start_at = db.Column(db.DateTime, default=now_jakarta)

    match_details = db.relationship("MatchDetail", backref="drawing", cascade="all, delete-orphan")


class MatchDetail(db.Model):
    __tablename__ = "match_details"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    match_id = db.Column(db.String(32), db.ForeignKey("drawing.match_id"), nullable=False)

    player_id = db.Column(db.String(10), nullable=False)
    team_side = db.Column(db.String(5), nullable=False)  # "A" or "B"
    team_side_score = db.Column(db.Integer, default=0)
    winner_flag = db.Column(db.String(1), nullable=True)  # W / L / T

    match_start_at = db.Column(db.DateTime, default=now_jakarta)
    match_end_at = db.Column(db.DateTime, nullable=True)
    match_duration = db.Column(db.String(20), nullable=True)  # HH:MM:SS

    def end_match(self):
        """Mark this match detail as ended and calculate duration."""
        self.match_end_at = now_jakarta()
        if self.match_start_at:
            delta = self.match_end_at - self.match_start_at
            self.match_duration = str(delta).split(".")[0]
        else:
            self.match_duration = None
