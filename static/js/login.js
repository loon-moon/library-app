(function () {
  "use strict";

  var form = document.getElementById("login-form");
  var usernameInput = document.getElementById("username");
  var passwordInput = document.getElementById("password");
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
    submitButton.textContent = busy ? "Вход..." : "Войти";
  }

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    hideError();

    var username = usernameInput.value.trim();
    var password = passwordInput.value;

    if (!username || !password) {
      showError("Введите логин и пароль.");
      return;
    }

    setBusy(true);
    try {
      await API.post("/api/auth/login", {
        username: username,
        password: password
      });
      window.location.replace("/");
    } catch (error) {
      showError(
        error.status === 401 ? "Неверный логин или пароль." : error.message
      );
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
