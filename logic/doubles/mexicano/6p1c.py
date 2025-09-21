import random

MAX_CONSECUTIVE = 2


def _consecutive_games(player: str, games: list[dict]) -> int:
    count = 0
    for game in reversed(games):
        teams = game.get("teams") or []
        if any(player in team for team in teams):
            count += 1
        else:
            break
    return count


def _flatten(game: dict) -> list[str]:
    teams = game.get("teams") or []
    flat = []
    for team in teams:
        flat.extend(team)
    return flat

def _ensure_four(selected: list[str], players: list[str]) -> list[str]:
    pool = [p for p in players if p not in selected]
    random.shuffle(pool)
    while len(selected) < 4 and pool:
        selected.append(pool.pop())
    if len(selected) < 4:
        # last resort: allow duplicates removal by restarting from scratch
        shuffled = players[:]
        random.shuffle(shuffled)
        selected = shuffled[:4]
    return selected[:4]


def next_game(players, games, force_no=None):
    """Generate next game for 6 players (1 court) with winner-stay Mexicano rule."""

    if len(players) < 4:
        raise ValueError("Mexicano doubles requires at least 4 players")

    if force_no is not None:
        game_no = force_no
    elif games:
        game_no = games[-1].get("game_no", len(games)) + 1
    else:
        game_no = 1

    # First game is a simple shuffle
    if not games:
        shuffled = players[:]
        random.shuffle(shuffled)
        return {
            "game_no": game_no,
            "teams": [shuffled[:2], shuffled[2:4]],
        }

    last_game = games[-1]
    last_players = _flatten(last_game)
    if len(last_players) < 4:
        shuffled = players[:]
        random.shuffle(shuffled)
        return {
            "game_no": game_no,
            "teams": [shuffled[:2], shuffled[2:4]],
        }

    winner_side = last_game.get("winner")
    teams = last_game.get("teams") or []
    if winner_side in {"A", "B"}:
        winners = list(teams[0 if winner_side == "A" else 1])
    else:
        winners = list(teams[0]) if teams else []

    losers = [p for p in last_players if p not in winners]
    bench_players = [p for p in players if p not in last_players]

    consec = {p: _consecutive_games(p, games) for p in players}

    stay_players = []
    resting_winners = []
    for winner in winners:
        if consec.get(winner, 0) >= MAX_CONSECUTIVE:
            resting_winners.append(winner)
        else:
            stay_players.append(winner)

    selected = stay_players[:]

    def pick_from_pool(pool, allow_limit=False):
        nonlocal selected
        for player in pool:
            if player in selected:
                continue
            if not allow_limit and consec.get(player, 0) >= MAX_CONSECUTIVE:
                continue
            selected.append(player)
            if len(selected) == 4:
                return True
        return False

    primary_pool = [p for p in bench_players if p not in selected]
    pick_from_pool(primary_pool)

    if len(selected) < 4:
        pick_from_pool(primary_pool, allow_limit=True)

    if len(selected) < 4:
        loser_pool = [p for p in losers if p not in selected]
        pick_from_pool(loser_pool)

    if len(selected) < 4:
        loser_pool_limit = [p for p in losers if p not in selected]
        pick_from_pool(loser_pool_limit, allow_limit=True)

    if len(selected) < 4:
        rest_pool = [p for p in players if p not in selected]
        pick_from_pool(rest_pool, allow_limit=True)

    if len(selected) < 4:
        selected = _ensure_four(selected, players)

    stay_lookup = set(stay_players)
    team_a = []
    team_b = []

    for winner in stay_players[:2]:
        if not team_a:
            team_a.append(winner)
        elif not team_b:
            team_b.append(winner)

    others = [p for p in selected if p not in set(team_a + team_b)]
    random.shuffle(others)

    for player in others:
        if len(team_a) < 2:
            team_a.append(player)
        else:
            team_b.append(player)

    while len(team_b) < 2 and len(team_a) > 1:
        team_b.append(team_a.pop())

    if len(team_a) < 2 or len(team_b) < 2:
        fallback = selected[:]
        fallback = _ensure_four(fallback, players)
        team_a = fallback[:2]
        team_b = fallback[2:4]

    return {
        "game_no": game_no,
        "teams": [team_a, team_b],
    }
