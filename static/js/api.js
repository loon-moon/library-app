(function () {
  "use strict";

  class ApiError extends Error {
    constructor(status, message) {
      super(message);
      this.name = "ApiError";
      this.status = status;
    }
  }

  function formatDetail(data) {
    if (data === null || data === undefined) {
      return "Неизвестная ошибка";
    }
    if (typeof data === "string") {
      return data;
    }
    if (Array.isArray(data.detail)) {
      return data.detail
        .map(function (item) {
          var location = Array.isArray(item.loc)
            ? item.loc
                .filter(function (part) {
                  return part !== "body";
                })
                .join(".")
            : "";
          var message = item.msg || "Ошибка валидации";
          return location ? location + ": " + message : message;
        })
        .join("; ");
    }
    if (typeof data.detail === "string") {
      return data.detail;
    }
    return JSON.stringify(data);
  }

  async function request(path, options) {
    var config = Object.assign(
      { credentials: "same-origin", method: "GET" },
      options || {}
    );
    var headers = Object.assign({}, config.headers || {});

    if (config.body !== undefined && config.body !== null) {
      if (typeof config.body !== "string") {
        config.body = JSON.stringify(config.body);
      }
      if (!headers["Content-Type"]) {
        headers["Content-Type"] = "application/json";
      }
    }
    config.headers = headers;

    var response;
    try {
      response = await fetch(path, config);
    } catch (error) {
      throw new ApiError(
        0,
        "Не удалось подключиться к серверу. Проверьте соединение."
      );
    }

    if (response.status === 204) {
      return null;
    }

    var text = await response.text();
    var data = null;
    if (text) {
      try {
        data = JSON.parse(text);
      } catch (error) {
        data = text;
      }
    }

    if (!response.ok) {
      throw new ApiError(response.status, formatDetail(data));
    }

    return data;
  }

  window.ApiError = ApiError;
  window.API = {
    get: function (path) {
      return request(path);
    },
    post: function (path, body) {
      return request(path, { method: "POST", body: body });
    },
    patch: function (path, body) {
      return request(path, { method: "PATCH", body: body });
    },
    delete: function (path) {
      return request(path, { method: "DELETE" });
    }
  };
})();
