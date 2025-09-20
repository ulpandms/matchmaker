let scoreA = initialScoreA;
let scoreB = initialScoreB;
const limit = pointLimit;
const durationEl = document.getElementById("duration");
const nextBtn = document.getElementById("nextBtn");
const teamABox = document.querySelector(".team-a-score");
const teamBBox = document.querySelector(".team-b-score");
const winnerMsg = document.getElementById("winner-msg");

let timer = null;

// Resume timer based on start_time from server
function startTimer() {
  const start = new Date(startTime);
  timer = setInterval(() => {
    const now = new Date();
    const diff = Math.floor((now - start) / 1000);
    const mins = Math.floor(diff / 60);
    const secs = diff % 60;
    durationEl.textContent = `${mins}’${secs.toString().padStart(2, "0")}`;
  }, 1000);
}
startTimer();

function syncScore() {
  fetch("/update-score", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({scoreA, scoreB})
  });
}

function changeScore(team, delta) {
  if (team === "A") {
    scoreA = Math.max(0, Math.min(limit, scoreA + delta));
    document.getElementById("scoreA").textContent = scoreA;
  } else {
    scoreB = Math.max(0, Math.min(limit, scoreB + delta));
    document.getElementById("scoreB").textContent = scoreB;
  }
  syncScore();
}

function endGame() {
  clearInterval(timer);
  let winnerText = "";
  let winnerTeam, loserTeam;

  if (scoreA > scoreB) {
    teamABox.classList.add("winner");
    teamBBox.classList.add("loser");
    winnerText = `Team A: ${teamA[0]} + ${teamA[1]}`;
    winnerTeam = "A"; loserTeam = "B";
  } else if (scoreB > scoreA) {
    teamBBox.classList.add("winner");
    teamABox.classList.add("loser");
    winnerText = `Team B: ${teamB[0]} + ${teamB[1]}`;
    winnerTeam = "B"; loserTeam = "A";
  } else {
    winnerText = "It's a tie!";
  }

  winnerMsg.innerHTML = `The Winner is ${winnerText}`;
  nextBtn.disabled = false;

  fetch("/end-match", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({winner: winnerTeam, loser: loserTeam, scoreA, scoreB})
  });
}

function nextMatch() {
  fetch("/next-match", {method: "POST"}).then(() => {
    window.location.href = "/drawing";
  });
}
