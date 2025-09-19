document.addEventListener("DOMContentLoaded", () => {
  const inputs = document.querySelectorAll(".input-wrapper input");
  const submitBtn = document.querySelector(".btn-submit");

  function validateForm() {
    let allValid = true;

    inputs.forEach(input => {
      if (input.type === "email") {
        const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.value.trim());
        if (!emailValid) allValid = false;
      } else {
        if (input.value.trim() === "") allValid = false;
      }
    });

    if (allValid) {
      submitBtn.classList.add("active");
      submitBtn.disabled = false;   // ✅ FIX: enable submit
    } else {
      submitBtn.classList.remove("active");
      submitBtn.disabled = true;    // ✅ FIX: keep disabled
    }
  }

  inputs.forEach(input => {
    input.addEventListener("input", () => {
      const wrapper = input.closest(".input-wrapper");

      if (input.type === "email") {
        const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.value.trim());
        wrapper.classList.toggle("filled", emailValid);
      } else {
        wrapper.classList.toggle("filled", input.value.trim() !== "");
      }

      validateForm();
    });
  });

  // Initial check on page load
  validateForm();
});
