document.addEventListener("DOMContentLoaded", () => {
  // players now injected from Flask (see drawing.html)
  const gameArea = document.getElementById("game-area");
  const redrawBtn = document.getElementById("redraw-btn");

  let lastGames = []; // track last N games for consecutive rule
  const maxConsec = 2;

  function shuffle(arr) {
    return arr
      .map(v => ({ v, sort: Math.random() }))
      .sort((a, b) => a.sort - b.sort)
      .map(({ v }) => v);
  }

  function pickTeams() {
    let shuffled = shuffle(players);

    // ensure no player exceeds consecutive limit
    let tries = 0;
    while (tries < 20) {
      let team1 = shuffled.slice(0, 2);
      let team2 = shuffled.slice(2, 4);

      if (isValid(team1, team2)) {
        return { team1, team2 };
      }
      shuffled = shuffle(players);
      tries++;
    }
    return { team1: shuffled.slice(0, 2), team2: shuffled.slice(2, 4) };
  }

  function isValid(team1, team2) {
    const game = [...team1, ...team2];
    for (let p of game) {
      let count = lastGames.slice(-maxConsec).flat().filter(x => x === p).length;
      if (count >= maxConsec) return false;
    }
    return true;
  }

  function renderGame(gameNumber = 1, court = "A") {
    const { team1, team2 } = pickTeams();

    // save game to history
    lastGames.push([...team1, ...team2]);

    gameArea.innerHTML = `
      <div class="game-block">
        <div class="game-title">Game #${gameNumber}</div>
        <div class="game-subtitle">(court ${court})</div>
        <div class="team">${team1.join(" + ")}</div>
        <div class="vs">Vs</div>
        <div class="team">${team2.join(" + ")}</div>
      </div>
    `;
  }

  redrawBtn.addEventListener("click", () => {
    renderGame();
  });

  // initial draw
  renderGame();
});