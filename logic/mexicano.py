import random

def create_intro_round(players):
    """Split 8 players into 2 games of 4 players."""
    shuffled = players[:]
    random.shuffle(shuffled)
    game1 = [shuffled[0:2], shuffled[2:4]]
    game2 = [shuffled[4:6], shuffled[6:8]]
    return game1, game2

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
        g1, _ = create_intro_round(players)
        return {"game_no": 1, "teams": g1}
    elif len(games) == 1:
        _, g2 = create_intro_round(players)
        return {"game_no": 2, "teams": g2}
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
