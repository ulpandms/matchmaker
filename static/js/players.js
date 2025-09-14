document.addEventListener("DOMContentLoaded", () => {
  const squadContainer = document.querySelector(".squad");
  const totalDisplay = document.querySelector(".total span");
  const startBtn = document.querySelector(".btn-submit");

  function updateTotal() {
    const filled = squadContainer.querySelectorAll(".input-wrapper.filled").length;
    totalDisplay.textContent = filled;

    // enable start button if 2 or more players
    if (filled >= 2) {
      startBtn.disabled = false;
      startBtn.classList.add("active");
    } else {
      startBtn.disabled = true;
      startBtn.classList.remove("active");
    }
  }

  function refreshPlayerLabels() {
    squadContainer.querySelectorAll(".player-row").forEach((row, idx) => {
      row.querySelector(".player-label").textContent = `P-${String(idx + 1).padStart(2, "0")}`;
    });
  }

  function refreshPlusButtons() {
    squadContainer.querySelectorAll(".add-btn").forEach(btn => btn.style.display = "none");
    const lastRow = squadContainer.querySelector(".player-row:last-child .add-btn");
    if (lastRow) lastRow.style.display = "inline-block";
  }

  function attachEvents(row) {
    const input = row.querySelector("input");
    const wrapper = row.querySelector(".input-wrapper");
    const checkIcon = row.querySelector(".check-icon");
    const addBtn = row.querySelector(".add-btn");

    // Input typing → show ✓
    input.addEventListener("input", () => {
      if (input.value.trim() !== "") {
        wrapper.classList.add("filled");
        checkIcon.textContent = "✓";
        checkIcon.style.borderColor = "#ff7a00";
        checkIcon.style.color = "#ff7a00";
      } else {
        wrapper.classList.remove("filled");
        checkIcon.textContent = "✓";
      }
      updateTotal();
    });

    // Circle click → toggle delete mode or delete
    checkIcon.addEventListener("click", () => {
      if (!wrapper.classList.contains("filled")) return;

      if (checkIcon.textContent === "✓") {
        // switch to delete mode
        checkIcon.textContent = "−";
        checkIcon.style.borderColor = "red";
        checkIcon.style.color = "red";
      } else {
        // prevent deleting if only 2 players remain
        const rows = squadContainer.querySelectorAll(".player-row").length;
        if (rows <= 2) {
          alert("At least 2 players are required.");
          // reset back to ✓
          checkIcon.textContent = "✓";
          checkIcon.style.borderColor = "#ff7a00";
          checkIcon.style.color = "#ff7a00";
          return;
        }

        // delete this row
        row.remove();
        refreshPlayerLabels();
        refreshPlusButtons();
        updateTotal();
      }
    });

    // Add button → new row
    if (addBtn) {
      addBtn.addEventListener("click", () => {
        addPlayerRow();
      });
    }
  }

  function addPlayerRow() {
    const index = squadContainer.querySelectorAll(".player-row").length + 1;

    const row = document.createElement("div");
    row.classList.add("player-row");

    row.innerHTML = `
      <div class="player-label">P-${String(index).padStart(2, "0")}</div>
      <div class="input-wrapper">
        <input type="text" placeholder="Player Name">
        <div class="check-icon">✓</div>
      </div>
      <button type="button" class="add-btn">+</button>
    `;

    squadContainer.appendChild(row);
    attachEvents(row);
    refreshPlusButtons();
  }

  // Init existing rows
  squadContainer.querySelectorAll(".player-row").forEach(row => attachEvents(row));

  refreshPlusButtons();
  updateTotal();
});
