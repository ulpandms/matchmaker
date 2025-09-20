let scoreA = initialScoreA;
let scoreB = initialScoreB;
let seconds = 0;
let timer = null;

const durationEl = document.getElementById("duration");
const nextBtn = document.getElementById("nextBtn");
const teamABox = document.querySelector(".team-a-score");
const teamBBox = document.querySelector(".team-b-score");
const winnerMsg = document.getElementById("winner-msg");

// Restore elapsed duration
function restoreTimer() {
  const now = new Date();
  seconds = Math.floor((now - startTime) / 1000);
  updateDuration();
  timer = setInterval(() => {
    seconds++;
    updateDuration();
  }, 1000);
}

function updateDuration() {
  let mins = Math.floor(seconds / 60);
  let secs = seconds % 60;
  durationEl.textContent = `${mins}’${secs.toString().padStart(2, "0")}`;
}

function renderScores() {
  document.getElementById("scoreA").textContent = scoreA;
  document.getElementById("scoreB").textContent = scoreB;
}

function persistScores() {
  fetch("/update-score", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scoreA, scoreB }),
  });
}

function changeScore(team, delta) {
  if (team === "A") {
    scoreA = Math.max(0, Math.min(pointLimit, scoreA + delta));
  } else {
    scoreB = Math.max(0, Math.min(pointLimit, scoreB + delta));
  }
  renderScores();
  persistScores();
}

function endGame() {
  clearInterval(timer);
  let winnerText = "";

  if (scoreA > scoreB) {
    teamABox.classList.add("winner");
    teamBBox.classList.add("loser");
    winnerText = `Team A: ${teamA[0]} + ${teamA[1]}`;
  } else if (scoreB > scoreA) {
    teamBBox.classList.add("winner");
    teamABox.classList.add("loser");
    winnerText = `Team B: ${teamB[0]} + ${teamB[1]}`;
  } else {
    winnerText = "It's a tie!";
  }

  winnerMsg.innerHTML = `The Winner is ${winnerText} 
    <span class="edit-icon">
      <img src="/static/images/pencil.svg" alt="Edit">
    </span>`;

  winnerMsg.querySelector(".edit-icon").addEventListener("click", () => {
    teamABox.classList.remove("winner", "loser");
    teamBBox.classList.remove("winner", "loser");
    winnerMsg.textContent = "";
    nextBtn.disabled = true;
    restoreTimer();
  });

  nextBtn.disabled = false;
}

function nextMatch() {
  window.location.href = "/drawing";
}

renderScores();
restoreTimer();
