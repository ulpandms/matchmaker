from flask import Flask, render_template, request, redirect, url_for, session
from flask_migrate import Migrate
from models import db, GameInfo, Playground, Player, GameDetail
from logic.loader import load_logic
import datetime

app = Flask(__name__)
app.secret_key = "dev"

# Configure SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///matchmaker.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Bind db + migrations
db.init_app(app)
migrate = Migrate(app, db)


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
            game_name=match_name,
            game_place=court,
            host_email=email
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
    if request.method == "POST":
        game_id = session.get("current_game_id")
        if not game_id:
            return redirect(url_for("game_plan"))

        players = [v for k, v in request.form.items() if k.startswith("player_") and v.strip()]
        session["players"] = [{"player_code": f"P-{i:02}", "player_name": name}
                              for i, name in enumerate(players, start=1)]

        return redirect(url_for("drawing"))

    return render_template("players.html")


@app.route("/drawing", methods=["GET", "POST"])
def drawing():
    game_id = session.get("current_game_id")
    if not game_id:
        return redirect(url_for("game_plan"))

    players = [p["player_name"] for p in session.get("players", [])]
    if not players:
        return redirect(url_for("players"))

    if "games" not in session:
        session["games"] = []

    games = session["games"]
    logic = get_logic()
    if not logic:
        return "No matching game logic found", 500

    if request.method == "POST":
        action = request.form.get("action")

        if action == "redraw":
            if games:
                last_no = games[-1]["game_no"]
                new_game = logic.next_game(players, games[:-1])
                if new_game:
                    new_game["game_no"] = last_no
                    games[-1] = new_game
        elif action == "next":
            new_game = logic.next_game(players, games)
            if new_game:
                games.append(new_game)
            session["games"] = games
            return redirect(url_for("game_session"))

        session["games"] = games
        return redirect(url_for("drawing"))

    # ✅ pass players here
    return render_template("drawing.html", games=games, players=players)



# ---------- Game Session ----------
@app.route("/game-session", methods=["GET", "POST"])
def game_session():
    games = session.get("games", [])
    if not games:
        return redirect(url_for("drawing"))

    current_game = games[-1]

    if request.method == "POST":
        winner = request.form.get("winner")
        if winner:
            if winner == "A":
                current_game["winner_players"] = current_game["teams"][0]
                current_game["loser_players"] = current_game["teams"][1]
            elif winner == "B":
                current_game["winner_players"] = current_game["teams"][1]
                current_game["loser_players"] = current_game["teams"][0]

        session["games"][-1] = current_game
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
