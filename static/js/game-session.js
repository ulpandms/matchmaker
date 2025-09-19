let scoreA = 0;
let scoreB = 0;
let startTime = new Date();

function changeScore(team, delta) {
  if (team === "A") {
    scoreA = Math.max(0, scoreA + delta);
    document.getElementById("scoreA").textContent = scoreA;
  } else {
    scoreB = Math.max(0, scoreB + delta);
    document.getElementById("scoreB").textContent = scoreB;
  }
}

function updateDuration() {
  const now = new Date();
  const diff = Math.floor((now - startTime) / 60000); // minutes
  document.getElementById("duration").textContent = `${diff}’`;
}
setInterval(updateDuration, 60000); // update every minute

function endGame() {
  alert(`Game Ended. Final Score: ${scoreA} - ${scoreB}`);
  // Later: send POST to server
}

function nextMatch() {
  alert("Proceeding to Next Match...");
  // Later: redirect or request new drawing
}
