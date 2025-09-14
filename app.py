from flask import Flask, render_template, request, redirect, url_for, session
from logic.mexicano import next_game, record_result

app = Flask(__name__)
app.secret_key = "dev"  # replace with secure key in production

@app.route("/")
def home():
    return render_template("index.html")

# -------------------- Game Plan --------------------
@app.route("/game-plan", methods=["GET", "POST"])
def game_plan():
    if request.method == "POST":
        match_name = request.form.get("match_name")
        court = request.form.get("court")
        email = request.form.get("email")
        print(f"[Game Plan] Match: {match_name}, Court: {court}, Email: {email}")

        # Save into session
        session["event"] = {"match_name": match_name, "court": court, "email": email}

        return redirect(url_for("playground"))

    return render_template("game-plan.html")

# -------------------- Playground --------------------
@app.route("/playground", methods=["GET", "POST"])
def playground():
    if request.method == "POST":
        sport = request.form.get("sport")
        format_ = request.form.get("format")   # avoid reserved word
        points = request.form.get("points")
        courts = request.form.get("courts")
        print(f"[Playground] Sport: {sport}, Format: {format_}, Points: {points}, Courts: {courts}")

        # Save into session
        session["playground"] = {"sport": sport, "format": format_, "points": points, "courts": courts}

        return redirect(url_for("players"))

    return render_template("playground.html")

# -------------------- Players --------------------
@app.route("/players", methods=["GET", "POST"])
def players():
    if request.method == "POST":
        # Collect player inputs dynamically
        players = [v for k, v in request.form.items() if k.startswith("player_") and v.strip()]
        print(f"[Players] Squad: {players}")

        # Save players and reset games
        session["players"] = players
        session["games"] = []

        return redirect(url_for("drawing"))

    return render_template("players.html")

# -------------------- Drawing --------------------
@app.route("/drawing", methods=["GET", "POST"])
def drawing():
    players = session.get("players", [])
    games = session.get("games", [])

    if request.method == "POST":
        action = request.form.get("action")

        if action == "next":
            # Record dummy result if needed (for now, always team 0 wins)
            if games and "winner" not in games[-1]:
                record_result(games[-1], winner_team_index=0)

            game = next_game(players, games)
            if game:
                games.append(game)
                session["games"] = games

        elif action == "redraw":
            if games:
                import random
                current = games[-1]
                flat = [p for t in current["teams"] for p in t]
                random.shuffle(flat)
                current["teams"] = [flat[:2], flat[2:4]]
                session["games"] = games

        return redirect(url_for("drawing"))

    return render_template("drawing.html", games=games)

# -------------------- Run --------------------
if __name__ == "__main__":
    app.run(debug=True)
