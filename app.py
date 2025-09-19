# app.py
from flask import Flask, render_template, request, redirect, url_for, session
from flask_migrate import Migrate   # NEW
from models import db, GameInfo, Playground, Player, GameDetail

app = Flask(__name__)
app.secret_key = "dev"

# Configure SQLite (instance folder keeps DB safe)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///matchmaker.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Bind db to app
db.init_app(app)

# Initialize migration
migrate = Migrate(app, db)   # NEW

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

        # Save to session so we can use it later
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

        # Collect dynamic players from form
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
        return redirect(url_for("game_plan"))

    if request.method == "POST":
        # Later handle storing matches into Game table
        return redirect(url_for("home"))

    return render_template("drawing.html")

# ---------- Game Session ----------
@app.route("/game-session", methods=["GET", "POST"])
def game_session():
    game_id = session.get("current_game_id")
    if not game_id:
        return redirect(url_for("game_plan"))

    # For now: hardcoded demo UI
    if request.method == "POST":
        # TODO: Save scores, update GameDetail table
        pass

    return render_template("game-session.html")

# -------------------- Run --------------------
if __name__ == "__main__":
    app.run(debug=True)
