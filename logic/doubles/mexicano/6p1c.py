import random

def next_game(players, games, force_no=None):
    """
    Generate next game for 6 players, 1 court, Mexicano rules.
    - Winner stays but split
    - Max 2 consecutive games
    """

    # Determine game number
    if force_no is not None:
        game_no = force_no
    elif games:
        game_no = games[-1]["game_no"] + 1
    else:
        game_no = 1

    # First game: random shuffle
    if not games:
        shuffled = players[:]
        random.shuffle(shuffled)
        return {
            "game_no": game_no,
            "teams": [shuffled[:2], shuffled[2:4]]
        }

    # Otherwise: winner stays but split, bring 2 new players
    last_game = games[-1]
    last_teams = last_game["teams"]

    # For demo: just split last game's Team A into separate sides
    stayers = [last_teams[0][0], last_teams[1][0]]  # split players
    others = [p for p in players if p not in last_teams[0] + last_teams[1]]
    random.shuffle(others)

    return {
        "game_no": game_no,
        "teams": [[stayers[0], others[0]], [stayers[1], others[1]]]
    }
