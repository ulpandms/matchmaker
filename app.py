from flask import Flask, render_template, request, redirect, url_for, session
from flask_migrate import Migrate
from models import db, GameInfo, Playground, Player, Drawing, MatchDetail
from logic.loader import load_logic
from datetime import datetime
from zoneinfo import ZoneInfo
import uuid

# -------------------- Config --------------------
app = Flask(__name__)
app.secret_key = "dev"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///matchmaker.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate = Migrate(app, db)

# Always use Jakarta timezone (GMT+7)
TZ = ZoneInfo("Asia/Jakarta")

def now_jakarta():
    """Return current datetime in Asia/Jakarta tz (GMT+7)."""
    return datetime.now(TZ)

# -------------------- Helpers --------------------
def get_logic():
    """Load logic module based on current playground & players."""
    players = session.get("players", [])
    players_count = len(players)

    game_id = session.get("current_game_id")
    if not game_id:
        return None

    playground = Playground.query.filter_by(game_id=game_id).first()
    if not playground:
        return None

    return load_logic(
        playground.game_type,
        playground.game_format,
        players_count,
        playground.courts_count
    )

# -------------------- Routes --------------------
@app.route("/")
def home():
    return render_template("index.html")

# ---------- Game Plan ----------
@app.route("/game-plan", methods=["GET", "POST"])
def game_plan():
    if request.method == "POST":
        match_name = request.form.get("game_name")
        court = request.form.get("game_place")
        email = request.form.get("host_email")

        new_game = GameInfo(
            game_id=str(uuid.uuid4().hex[:24]),
            game_name=match_name,
            game_place=court,
            host_email=email,
            created_at=now_jakarta()  # ✅ GMT+7
        )
        db.session.add(new_game)
        db.session.commit()

        session["current_game_id"] = new_game.game_id
        return redirect(url_for("playground"))

    return render_template("game-plan.html")

# ---------- Playground ----------
@app.route("/playground", methods=["GET", "POST"])
def playground():
    if request.method == "POST":
        sport = request.form.get("sport")
        game_type = request.form.get("game_type")
        game_format = request.form.get("game_format")
        point_limit = request.form.get("point_limit")
        courts_count = request.form.get("courts_count")

        game_id = session.get("current_game_id")
        if not game_id:
            return redirect(url_for("game_plan"))

        new_playground = Playground(
            game_id=game_id,
            sport=sport,
            game_type=game_type,
            game_format=game_format,
            point_limit=int(point_limit),
            courts_count=int(courts_count)
        )
        db.session.add(new_playground)
        db.session.commit()

        session["point_limit"] = int(point_limit)
        return redirect(url_for("players"))

    return render_template("playground.html")

# ---------- Players ----------
@app.route("/players", methods=["GET", "POST"])
def players():
    game_id = session.get("current_game_id")
    if not game_id:
        return redirect(url_for("game_plan"))

    if request.method == "POST":
        # Clear any old players for this game (safety when re-entering)
        Player.query.filter_by(game_id=game_id).delete()

        # Collect dynamic players from form
        form_players = [v for k, v in request.form.items() if k.startswith("player_") and v.strip()]

        for idx, name in enumerate(form_players, start=1):
            player = Player(
                player_code=f"P-{idx:02}",
                player_name=name,
                game_id=game_id
            )
            db.session.add(player)

        db.session.commit()
        print(f"✅ [DB] {len(form_players)} players saved for game {game_id}")

        # After players saved, jump to drawing page
        return redirect(url_for("drawing"))

    return render_template("players.html")

# ---------- Drawing ----------
@app.route("/drawing", methods=["GET", "POST"])
def drawing():
    game_id = session.get("current_game_id")
    if not game_id:
        return redirect(url_for("game_plan"))

    # ✅ Always load players from DB
    players_db = Player.query.filter_by(game_id=game_id).all()
    players = [p.player_name for p in players_db]

    if not players:
        return redirect(url_for("players"))

    if "games" not in session:
        session["games"] = []

    games = session["games"]
    logic = get_logic()
    if not logic:
        return "No matching game logic found", 500

    # ✅ If no games yet, auto-generate the first one
    if not games:
        first_game = logic.next_game(players, [])
        if first_game:
            games.append(first_game)
            session["games"] = games

    if request.method == "POST":
        action = request.form.get("action")

        if action == "redraw":
            if games:
                # reshuffle but keep same game_no
                games[-1] = logic.next_game(players, games[:-1],
                                            force_no=games[-1]["game_no"])
        elif action == "next":
            new_game = logic.next_game(players, games)
            if new_game:
                # Store drawing rows into DB
                for side, team in enumerate(new_game["teams"], start=1):
                    for idx, player_name in enumerate(team, start=1):
                        player_obj = next((p for p in players_db if p.player_name == player_name), None)
                        drawing_row = Drawing(
                            game_id=game_id,
                            game_no=new_game["game_no"],
                            court_no="A",  # still only 1 court
                            team_side=f"Team {side}",
                            player_code=player_obj.player_code if player_obj else f"P-{idx:02}",
                            player_id=player_obj.player_id if player_obj else str(uuid.uuid4().hex[:10]),
                            player_match_number=idx,
                            match_id=new_game["match_id"],
                            match_start_at=new_game["start_time"]
                        )
                        db.session.add(drawing_row)
                db.session.commit()

                games.append(new_game)

            session["games"] = games
            return redirect(url_for("game_session"))

    return render_template("drawing.html", games=games, players=players)


# ---------- Game Session ----------
@app.route("/game-session", methods=["GET", "POST"])
def game_session():
    games = session.get("games", [])
    if not games:
        return redirect(url_for("drawing"))

    current_game = games[-1]

    if request.method == "POST":
        # Called when "End This Game" is clicked
        winner = request.form.get("winner")
        if winner:
            detail = MatchDetail(
                match_id=current_game["match_id"],
                team_side=winner,
                team_side_score=current_game.get("scoreA" if winner == "A" else "scoreB", 0),
                winner_flag="W",
                match_start_at=current_game.get("start_time", now_jakarta()),
                match_end_at=now_jakarta(),  # ✅ GMT+7
            )
            db.session.add(detail)
            db.session.commit()

        return redirect(url_for("drawing"))

    return render_template(
        "game-session.html",
        game_no=current_game["game_no"],
        team_a=current_game["teams"][0],
        team_b=current_game["teams"][1],
        point_limit=session.get("point_limit", 21),
        start_time=current_game.get("start_time"),
        scoreA=current_game.get("scoreA", 0),
        scoreB=current_game.get("scoreB", 0),
    )

# -------------------- Run --------------------
if __name__ == "__main__":
    app.run(debug=True)
