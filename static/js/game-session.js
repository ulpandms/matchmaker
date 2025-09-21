let scoreA = Number.isFinite(initialScoreA) ? initialScoreA : 0;
let scoreB = Number.isFinite(initialScoreB) ? initialScoreB : 0;
const limit = pointLimit || 21;

const durationEl = document.getElementById("duration");
const winnerField = document.getElementById("winnerField");
const scoreAField = document.getElementById("scoreAField");
const scoreBField = document.getElementById("scoreBField");
const endForm = document.getElementById("endForm");
const hasEnded = matchEnded === true || matchEnded === "true";

const baseElapsed = Number.isFinite(elapsedSeconds) ? elapsedSeconds : 0;
const resumeTimestamp = resumeTimeValue ? new Date(resumeTimeValue) : null;

function formatDuration(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function currentElapsedSeconds() {
  if (hasEnded) {
    return baseElapsed;
  }
  if (!resumeTimestamp) {
    return baseElapsed;
  }
  const now = new Date();
  const diffSeconds = Math.max(0, Math.floor((now - resumeTimestamp) / 1000));
  return baseElapsed + diffSeconds;
}

function updateDuration() {
  durationEl.textContent = formatDuration(currentElapsedSeconds());
}

if (!hasEnded) {
  updateDuration();
  setInterval(updateDuration, 1000);
} else {
  updateDuration();
}

function updateHiddenScores() {
  if (scoreAField) scoreAField.value = scoreA;
  if (scoreBField) scoreBField.value = scoreB;
}

function renderScores() {
  const scoreANode = document.getElementById("scoreA");
  const scoreBNode = document.getElementById("scoreB");
  if (scoreANode) scoreANode.textContent = scoreA;
  if (scoreBNode) scoreBNode.textContent = scoreB;
  updateHiddenScores();
}
renderScores();

function changeScore(team, delta) {
  if (hasEnded) return;
  if (team === 'A') {
    scoreA = Math.max(0, Math.min(limit, scoreA + delta));
  } else {
    scoreB = Math.max(0, Math.min(limit, scoreB + delta));
  }
  renderScores();
}

function prepareEndGame(evt) {
  if (hasEnded) {
    evt.preventDefault();
    return;
  }
  updateHiddenScores();
  if (!winnerField) {
    return;
  }
  let winner = 'T';
  if (scoreA > scoreB) {
    winner = 'A';
  } else if (scoreB > scoreA) {
    winner = 'B';
  }
  winnerField.value = winner;
}

window.changeScore = changeScore;
window.prepareEndGame = prepareEndGame;
