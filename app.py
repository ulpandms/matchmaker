from flask import Flask, render_template, request, redirect, url_for, session
from flask_migrate import Migrate
from models import db, GameInfo, Playground, Player, Drawing, MatchDetail
from logic.loader import load_logic
from datetime import datetime, timedelta
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

def to_jakarta_naive(dt: datetime) -> datetime:
    """Ensure datetime is naive in Jakarta timezone for DB storage."""
    if dt.tzinfo is not None:
        return dt.astimezone(TZ).replace(tzinfo=None)
    return dt


def finalize_game_result(game_id: str, active_game: dict):
    """Persist the active game's pending result and clear session state."""
    if not active_game or not active_game.get("result_pending"):
        return False, "End the current game before wrapping up."

    result = active_game["result_pending"]

    match_id = active_game.get("match_id") or uuid.uuid4().hex
    active_game["match_id"] = match_id

    start_iso = active_game.get("start_time")
    if isinstance(start_iso, datetime):
        start_iso = start_iso.isoformat()
        active_game["start_time"] = start_iso
    if not start_iso:
        start_iso = now_jakarta().isoformat()
        active_game["start_time"] = start_iso

    end_iso = result.get("ended_at") or now_jakarta().isoformat()
    result["ended_at"] = end_iso

    start_dt = to_jakarta_naive(datetime.fromisoformat(start_iso))
    end_dt = to_jakarta_naive(datetime.fromisoformat(end_iso))

    players_db = Player.query.filter_by(game_id=game_id).order_by(Player.player_code).all()
    players_map = {player.player_name: player for player in players_db}

    elapsed_total = int(active_game.get("elapsed_seconds", 0) or 0)
    duration_delta = timedelta(seconds=elapsed_total)
    duration_str = str(duration_delta).split(".")[0]

    for side_index, team in enumerate(active_game.get("teams", []), start=1):
        team_side = "A" if side_index == 1 else "B"
        score = result["scoreA"] if team_side == "A" else result["scoreB"]
        if result["winner"] == "T":
            flag = "T"
        else:
            flag = "W" if team_side == result["winner"] else "L"

        for player_name in team:
            player_obj = players_map.get(player_name)
            player_id = player_obj.player_id if player_obj else uuid.uuid4().hex[:10]
            detail = MatchDetail(
                match_id=match_id,
                player_id=player_id,
                team_side=team_side,
                team_side_score=score,
                winner_flag=flag,
                match_start_at=start_dt,
                match_end_at=end_dt,
                match_duration=duration_str,
            )
            db.session.add(detail)

    db.session.commit()

    locked_games = session.get("games") or []
    for idx, stored in enumerate(locked_games):
        if stored.get("match_id") == match_id:
            locked_games[idx] = active_game
            break
    else:
        locked_games.append(active_game)
    session["games"] = locked_games

    active_game["status"] = "completed"
    active_game["completed_at"] = end_iso
    active_game.pop("result_pending", None)

    session["active_game"] = None
    session["pending_game"] = None
    session.modified = True

    return True, None


# -------------------- Helpers --------------------
def get_logic():
    """Load logic module based on current playground & players."""
    game_id = session.get("current_game_id")
    if not game_id:
        return None

    players = session.get("players")
    if not players:
        players = [
            p.player_name
            for p in Player.query.filter_by(game_id=game_id).order_by(Player.player_code).all()
        ]
        if players:
            session["players"] = players
            session.modified = True

    players_count = len(players or [])
    if players_count == 0:
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

        session.clear()
        session["current_game_id"] = new_game.game_id
        session["games"] = []
        session["pending_game"] = None
        session["active_game"] = None
        session["players"] = []
        session.modified = True

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

        session["players"] = form_players
        session["games"] = []
        session["pending_game"] = None
        session["active_game"] = None
        session.modified = True

        # After players saved, jump to drawing page
        return redirect(url_for("drawing"))

    return render_template("players.html")

# ---------- Drawing ----------
@app.route("/drawing", methods=["GET", "POST"])
def drawing():
    game_id = session.get("current_game_id")
    if not game_id:
        return redirect(url_for("game_plan"))

    players_db = Player.query.filter_by(game_id=game_id).order_by(Player.player_code).all()
    players = [p.player_name for p in players_db]

    if not players:
        return redirect(url_for("players"))

    logic = get_logic()
    if not logic:
        return "No matching game logic found", 500

    locked_games = session.get("games") or []
    pending_game = session.get("pending_game")

    if not pending_game:
        next_number = len(locked_games) + 1
        candidate = logic.next_game(players, locked_games, force_no=next_number)
        if candidate:
            candidate.setdefault("teams", [])
            candidate["game_no"] = next_number
            pending_game = candidate
            session["pending_game"] = pending_game
            session.modified = True

    if request.method == "POST":
        action = request.form.get("action")

        if action == "redraw":
            if pending_game:
                force_no = pending_game.get("game_no") or len(locked_games) + 1
                candidate = logic.next_game(players, locked_games, force_no=force_no)
                if candidate:
                    candidate.setdefault("teams", [])
                    candidate["game_no"] = force_no
                    pending_game = candidate
                    session["pending_game"] = pending_game
                    session.modified = True
            return redirect(url_for("drawing"))

        if action == "next":
            if not pending_game:
                return redirect(url_for("drawing"))

            match_id = pending_game.get("match_id") or uuid.uuid4().hex
            start_time = pending_game.get("start_time")
            if isinstance(start_time, datetime):
                start_time = start_time.isoformat()
            if not start_time:
                start_time = now_jakarta().isoformat()

            pending_game["match_id"] = match_id
            pending_game["start_time"] = start_time
            pending_game.setdefault("scoreA", 0)
            pending_game.setdefault("scoreB", 0)
            pending_game.setdefault("elapsed_seconds", 0)
            pending_game["resume_time"] = start_time
            pending_game["status"] = "active"

            start_dt = to_jakarta_naive(datetime.fromisoformat(start_time))

            existing_draws = Drawing.query.filter_by(game_id=game_id).all()
            match_counts = {}
            for draw in existing_draws:
                match_counts[draw.player_id] = match_counts.get(draw.player_id, 0) + 1

            for side, team in enumerate(pending_game.get("teams", []), start=1):
                team_label = "A" if side == 1 else "B"
                for idx, player_name in enumerate(team, start=1):
                    player_obj = next((p for p in players_db if p.player_name == player_name), None)
                    player_code = player_obj.player_code if player_obj else f"P-{idx:02}"
                    player_id = player_obj.player_id if player_obj else uuid.uuid4().hex[:10]

                    match_counts[player_id] = match_counts.get(player_id, 0) + 1

                    drawing_row = Drawing(
                        game_id=game_id,
                        game_no=pending_game["game_no"],
                        court_no="A",  # TODO: support multiple courts
                        team_side=team_label,
                        player_code=player_code,
                        player_id=player_id,
                        player_match_number=match_counts[player_id],
                        match_id=match_id,
                        match_start_at=start_dt,
                    )
                    db.session.add(drawing_row)
            db.session.commit()

            locked_games.append(pending_game)
            session["games"] = locked_games
            session["active_game"] = pending_game
            session["pending_game"] = None
            session.modified = True

            return redirect(url_for("game_session"))

    return render_template(
        "drawing.html",
        players=players,
        pending_game=pending_game,
        games=locked_games,
    )


# ---------- Game Session ----------
@app.route("/game-session", methods=["GET", "POST"])
def game_session():
    active_game = session.get("active_game")
    if not active_game:
        return redirect(url_for("drawing"))

    game_id = session.get("current_game_id")
    if not game_id:
        return redirect(url_for("game_plan"))

    error_message = session.pop("wrap_up_error", None)
    ended = active_game.get("status") == "ended"
    winner_side = active_game.get("winner")
    loser_side = None
    if winner_side in {"A", "B"}:
        loser_side = "B" if winner_side == "A" else "A"

    if request.method == "POST":
        action = request.form.get("action")

        if action == "end":
            score_a = int(request.form.get("scoreA") or active_game.get("scoreA", 0) or 0)
            score_b = int(request.form.get("scoreB") or active_game.get("scoreB", 0) or 0)
            winner = request.form.get("winner")
            if winner not in {"A", "B", "T"}:
                if score_a > score_b:
                    winner = "A"
                elif score_b > score_a:
                    winner = "B"
                else:
                    winner = "T"

            end_dt = now_jakarta()
            ended_at = end_dt.isoformat()

            resume_iso = active_game.get("resume_time") or active_game.get("start_time")
            elapsed_total = int(active_game.get("elapsed_seconds", 0) or 0)
            if resume_iso:
                try:
                    resume_dt = datetime.fromisoformat(resume_iso)
                    elapsed_total += max(0, int((end_dt - resume_dt).total_seconds()))
                except ValueError:
                    pass
            active_game["elapsed_seconds"] = elapsed_total
            active_game["resume_time"] = None

            active_game["scoreA"] = score_a
            active_game["scoreB"] = score_b
            active_game["winner"] = winner
            active_game["status"] = "ended"
            active_game["ended_at"] = ended_at
            active_game["result_pending"] = {
                "winner": winner,
                "scoreA": score_a,
                "scoreB": score_b,
                "ended_at": ended_at,
                "elapsed_seconds": elapsed_total,
            }
            session["active_game"] = active_game
            session.modified = True

            ended = True
            winner_side = winner
            loser_side = None
            if winner_side in {"A", "B"}:
                loser_side = "B" if winner_side == "A" else "A"

        elif action == "revise":
            for key in ("status", "winner", "ended_at", "result_pending"):
                active_game.pop(key, None)
            active_game.setdefault("elapsed_seconds", 0)
            active_game["resume_time"] = now_jakarta().isoformat()
            active_game["status"] = "active"
            session["active_game"] = active_game
            session.modified = True
            ended = False
            winner_side = None
            loser_side = None

        elif action == "next":
            success, error = finalize_game_result(game_id, active_game)
            if not success:
                error_message = error
            else:
                return redirect(url_for("drawing"))

    ended = active_game.get("status") == "ended"
    winner_side = active_game.get("winner")
    loser_side = None
    if winner_side in {"A", "B"}:
        loser_side = "B" if winner_side == "A" else "A"

    teams = active_game.get("teams") or []

    def normalize_team(team):
        team_list = list(team or [])
        while len(team_list) < 2:
            team_list.append("-")
        return team_list[:2]

    team_a_names = normalize_team(teams[0] if len(teams) > 0 else [])
    team_b_names = normalize_team(teams[1] if len(teams) > 1 else [])

    return render_template(
        "game-session.html",
        game_no=active_game.get("game_no"),
        team_a=team_a_names,
        team_b=team_b_names,
        team_a_names=team_a_names,
        team_b_names=team_b_names,
        point_limit=session.get("point_limit", 21),
        start_time=active_game.get("start_time"),
        scoreA=int(active_game.get("scoreA", 0) or 0),
        scoreB=int(active_game.get("scoreB", 0) or 0),
        ended=ended,
        winner_side=winner_side,
        loser_side=loser_side,
        error_message=error_message,
        ended_at=active_game.get("ended_at"),
        elapsed_seconds=int(active_game.get("elapsed_seconds", 0) or 0),
        resume_time=active_game.get("resume_time") or active_game.get("start_time"),
    )



# ---------- Wrap Up ----------
@app.route("/wrap-up", methods=["POST"])
def wrap_up():
    game_id = session.get("current_game_id")
    if not game_id:
        return redirect(url_for("game_plan"))

    active_game = session.get("active_game")
    if active_game and active_game.get("result_pending"):
        success, error = finalize_game_result(game_id, active_game)
        if not success:
            session["wrap_up_error"] = error
            session.modified = True
            return redirect(url_for("game_session"))
    else:
        session["active_game"] = None
        session["pending_game"] = None

    session["event_completed"] = True
    session.modified = True

    return redirect(url_for("leaderboard"))


# ---------- Leaderboard ----------
@app.route("/leaderboard")
def leaderboard():
    game_id = request.args.get("game_id") or session.get("current_game_id")
    if not game_id:
        return redirect(url_for("game_plan"))

    game = GameInfo.query.filter_by(game_id=game_id).first()
    if not game:
        return redirect(url_for("game_plan"))

    players = Player.query.filter_by(game_id=game_id).order_by(Player.player_code).all()
    player_map = {
        player.player_id: {
            "name": player.player_name,
            "code": player.player_code,
        }
        for player in players
    }

    stats = {
        player_id: {
            "player_id": player_id,
            "player_code": data["code"],
            "player_name": data["name"],
            "games": 0,
            "wins": 0,
            "losses": 0,
            "ties": 0,
            "points": 0,
            "point_diff": 0,
        }
        for player_id, data in player_map.items()
    }

    details = (
        db.session.query(
            MatchDetail.match_id,
            MatchDetail.player_id,
            MatchDetail.team_side,
            MatchDetail.team_side_score,
            MatchDetail.winner_flag,
        )
        .join(
            Drawing,
            (MatchDetail.match_id == Drawing.match_id)
            & (MatchDetail.player_id == Drawing.player_id),
        )
        .filter(Drawing.game_id == game_id)
        .all()
    )

    match_scores = {}
    for detail in details:
        match_scores.setdefault(detail.match_id, {})[detail.team_side] = detail.team_side_score or 0

    for detail in details:
        player_id = detail.player_id
        player_stats = stats.setdefault(
            player_id,
            {
                "player_id": player_id,
                "player_code": player_id,
                "player_name": player_map.get(player_id, {}).get("name", "Unknown"),
                "games": 0,
                "wins": 0,
                "losses": 0,
                "ties": 0,
                "points": 0,
                "point_diff": 0,
            },
        )

        player_stats["games"] += 1
        flag = (detail.winner_flag or "").upper()
        if flag == "W":
            player_stats["wins"] += 1
        elif flag == "L":
            player_stats["losses"] += 1
        elif flag == "T":
            player_stats["ties"] += 1

        score = detail.team_side_score or 0
        player_stats["points"] += score

        opponent_side = "B" if detail.team_side == "A" else "A"
        opponent_score = match_scores.get(detail.match_id, {}).get(opponent_side, 0)
        player_stats["point_diff"] += score - opponent_score

    leaderboard_rows = sorted(
        stats.values(),
        key=lambda s: (s["points"], s["point_diff"], s["wins"]),
        reverse=True,
    )

    for idx, row in enumerate(leaderboard_rows, start=1):
        row["rank"] = idx

    return render_template(
        "leaderboard.html",
        leaderboard=leaderboard_rows,
        game_id=game_id,
        game_name=game.game_name,
        game_place=game.game_place,
        game_date=game.created_at,
        event_completed=session.get("event_completed", False),
    )

# -------------------- Run --------------------
if __name__ == "__main__":
    app.run(debug=True)
