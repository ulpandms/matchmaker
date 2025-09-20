# app.py
from flask import Flask, render_template, request, redirect, url_for, session
from flask_migrate import Migrate
from models import db, GameInfo, Playground, Player, GameDetail
from logic import mexicano
import datetime

app = Flask(__name__)
app.secret_key = "dev"

# Configure SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///matchmaker.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Bind db + migrations
db.init_app(app)
migrate = Migrate(app, db)


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
            game_name=match_name,
            game_place=court,
            host_email=email
        )
        db.session.add(new_game)
        db.session.commit()

        session["current_game_id"] = new_game.game_id
        print(f"[DB] New Game saved: {new_game.game_id}")

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

        print(f"[DB] Playground saved for game {game_id}")
        return redirect(url_for("players"))

    return render_template("playground.html")


# ---------- Players ----------
@app.route("/players", methods=["GET", "POST"])
def players():
    if request.method == "POST":
        game_id = session.get("current_game_id")
        if not game_id:
            return redirect(url_for("game_plan"))

        players = [v for k, v in request.form.items() if k.startswith("player_") and v.strip()]

        for idx, name in enumerate(players, start=1):
            player = Player(
                game_id=game_id,
                player_code=f"P-{idx:02}",
                player_name=name
            )
            db.session.add(player)

        db.session.commit()
        print(f"[DB] {len(players)} players saved for game {game_id}")

        return redirect(url_for("drawing"))

    return render_template("players.html")


# ---------- Drawing ----------
@app.route("/drawing", methods=["GET", "POST"])
def drawing():
    game_id = session.get("current_game_id")
    if not game_id:
        game_id = "TESTGAME1234567890123456"
        session["current_game_id"] = game_id

    # Mock players for now (replace later with DB)
    mock_players = [
        {"player_code": "P-01", "player_name": "Dimas"},
        {"player_code": "P-02", "player_name": "Ryan"},
        {"player_code": "P-03", "player_name": "Kenny"},
        {"player_code": "P-04", "player_name": "Steven"},
        {"player_code": "P-05", "player_name": "Yulius"},
        {"player_code": "P-06", "player_name": "Amin"},
    ]
    if "players" not in session:
        session["players"] = mock_players

    players = [p["player_name"] for p in session["players"]]

    if "games" not in session:
        session["games"] = []

    games = session["games"]

    if not games:
        first_game = mexicano.next_game(players, [])
        if first_game:
            games.append(first_game)
            session["games"] = games

    if request.method == "POST":
        action = request.form.get("action")

        if action == "redraw" and games:
            games[-1] = mexicano.next_game(players, games[:-1])

        elif action == "next":  # ✅ "Game On"
            current_game = games[-1]

            # Save teams into session for Game Session
            session["current_match"] = {
                "game_no": current_game["game_no"],
                "team_a": current_game["teams"][0],
                "team_b": current_game["teams"][1],
                "start_time": session.get("current_match", {}).get("start_time")
                               or datetime.datetime.now().isoformat(),  # persist start
                "ended": False
            }

            return redirect(url_for("game_session"))

        session["games"] = games
        return redirect(url_for("drawing"))

    return render_template("drawing.html", games=games)


# ---------- Game Session ----------
@app.route("/game-session", methods=["GET", "POST"])
def game_session():
    game_id = session.get("current_game_id")
    if not game_id:
        return redirect(url_for("game_plan"))

    last_game = session.get("games", [])[-1] if session.get("games") else None
    if not last_game:
        return redirect(url_for("drawing"))

    team_a = last_game["teams"][0]
    team_b = last_game["teams"][1]
    game_no = last_game["game_no"]

    # Ensure match state is initialized
    match_state = session.get("current_match", {})
    if "start_time" not in match_state:
        match_state["start_time"] = datetime.datetime.now().isoformat()
    if "scoreA" not in match_state:
        match_state["scoreA"] = 0
    if "scoreB" not in match_state:
        match_state["scoreB"] = 0

    session["current_match"] = match_state
    session.modified = True

    return render_template(
        "game-session.html",
        game_no=game_no,
        team_a=team_a,
        team_b=team_b,
        point_limit=session.get("point_limit", 21),
        start_time=match_state["start_time"],
        scoreA=match_state["scoreA"],
        scoreB=match_state["scoreB"],
    )


@app.route("/update-score", methods=["POST"])
def update_score():
    """AJAX endpoint to update score in session"""
    data = request.get_json()
    if "current_match" not in session:
        return {"ok": False}, 400

    session["current_match"]["scoreA"] = data.get("scoreA", 0)
    session["current_match"]["scoreB"] = data.get("scoreB", 0)
    session.modified = True
    return {"ok": True}

# -------------------- Run --------------------
if __name__ == "__main__":
    app.run(debug=True)
