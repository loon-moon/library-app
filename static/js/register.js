(function () {
  "use strict";

  var form = document.getElementById("register-form");
  var usernameInput = document.getElementById("username");
  var passwordInput = document.getElementById("password");
  var confirmInput = document.getElementById("password-confirm");
  var termsInput = document.getElementById("terms");
  var submitButton = document.getElementById("submit-btn");
  var errorBox = document.getElementById("form-error");

  function showError(message) {
    errorBox.textContent = message;
    errorBox.classList.remove("hidden");
  }

  function hideError() {
    errorBox.textContent = "";
    errorBox.classList.add("hidden");
  }

  function setBusy(busy) {
    submitButton.disabled = busy;
    submitButton.textContent = busy ? "Регистрация..." : "Зарегистрироваться";
  }

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    hideError();

    var username = usernameInput.value.trim();
    var password = passwordInput.value;
    var confirmation = confirmInput.value;

    if (username.length < 3) {
      showError("Логин должен содержать минимум 3 символа.");
      return;
    }
    if (password.length < 6) {
      showError("Пароль должен содержать минимум 6 символов.");
      return;
    }
    if (password !== confirmation) {
      showError("Пароли не совпадают.");
      return;
    }
    if (!termsInput.checked) {
      showError("Примите условия соглашения, чтобы продолжить.");
      return;
    }

    setBusy(true);
    try {
      await API.post("/api/auth/register", {
        username: username,
        password: password
      });
      window.location.replace("/");
    } catch (error) {
      showError(error.message);
      setBusy(false);
    }
  });

  (async function redirectIfAuthorized() {
    try {
      await API.get("/api/auth/me");
      window.location.replace("/");
    } catch (error) {
      if (error.status !== 401) {
        showError(error.message);
      }
    }
  })();
})();
