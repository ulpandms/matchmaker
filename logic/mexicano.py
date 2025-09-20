import random

def create_intro_round(players):
    """
    Create the first round(s) depending on number of players.
    For 8 players → 2 games of 4.
    For fewer players (like 6) → 1 game of 4, extras sit out.
    For more players → chunk them into groups of 4 as possible.
    """
    shuffled = players[:]
    random.shuffle(shuffled)

    games = []
    # break into chunks of 4
    for i in range(0, len(shuffled), 4):
        chunk = shuffled[i:i+4]
        if len(chunk) == 4:
            games.append([chunk[0:2], chunk[2:4]])

    return games


def record_result(game, winner_team_index):
    """Mark winner and loser in game dictionary."""
    winner = game["teams"][winner_team_index]
    loser = game["teams"][1 - winner_team_index]
    game["winner"] = winner
    game["loser"] = loser


def switch_partners(team1, team2):
    """Switch partners between two teams (Mexicano rule)."""
    return [[team1[0], team2[0]], [team1[1], team2[1]]]


def check_consecutive(games, new_game, limit=2):
    """Ensure no player exceeds consecutive play limit."""
    last_games = games[-limit:]
    players_recent = [p for g in last_games for t in g["teams"] for p in t]
    for team in new_game:
        for p in team:
            if players_recent.count(p) >= limit:
                return False
    return True


def next_game(players, games):
    """Generate the next game following Mexicano rules."""
    if len(games) == 0:
        intro_games = create_intro_round(players)
        if intro_games:
            return {"game_no": 1, "teams": intro_games[0]}
        return None

    elif len(games) == 1 and len(players) >= 8:
        intro_games = create_intro_round(players)
        if len(intro_games) > 1:
            return {"game_no": 2, "teams": intro_games[1]}
        return None

    elif len(games) == 2:
        g1, g2 = games[0], games[1]
        if "winner" in g1 and "winner" in g2:
            return {"game_no": 3, "teams": switch_partners(g1["winner"], g2["winner"])}
        return None

    elif len(games) == 3:
        g1, g2 = games[0], games[1]
        if "loser" in g1 and "loser" in g2:
            return {"game_no": 4, "teams": switch_partners(g1["loser"], g2["loser"])}
        return None

    else:
        tries = 0
        while tries < 20:
            shuffled = players[:]
            random.shuffle(shuffled)
            teams = [shuffled[:2], shuffled[2:4]]
            if check_consecutive(games, teams):
                return {"game_no": len(games)+1, "teams": teams}
            tries += 1
        return {"game_no": len(games)+1, "teams": [players[:2], players[2:4]]}
