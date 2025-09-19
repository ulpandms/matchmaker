document.addEventListener("DOMContentLoaded", () => {
  const inputs = document.querySelectorAll(".input-wrapper input");
  const submitBtn = document.querySelector(".btn-submit");

  function validateForm() {
    let allValid = true;

    inputs.forEach(input => {
      if (input.type === "email") {
        if (!input.value.includes("@")) {
          allValid = false;
        }
      } else {
        if (input.value.trim() === "") {
          allValid = false;
        }
      }
    });

    if (allValid) {
      submitBtn.classList.add("active");
    } else {
      submitBtn.classList.remove("active");
    }
  }

  inputs.forEach(input => {
    input.addEventListener("input", () => {
      if (input.type === "email") {
        if (input.value.includes("@")) {
          input.parentElement.classList.add("filled");
        } else {
          input.parentElement.classList.remove("filled");
        }
      } else {
        if (input.value.trim() !== "") {
          input.parentElement.classList.add("filled");
        } else {
          input.parentElement.classList.remove("filled");
        }
      }

      validateForm();
    });
  });

  // Initial check
  validateForm();
});