(function () {
  "use strict";

  var STATUS_LABELS = {
    want: "Хочу",
    reading: "Читаю",
    read: "Прочитано"
  };
  var PAGE_SIZE = 24;
  var RECOMMENDED_STEP = 7;

  var state = {
    user: null,
    genres: [],
    publishers: [],
    shelves: [],
    books: [],
    offset: 0,
    hasMore: false,
    recommended: [],
    recommendedVisible: RECOMMENDED_STEP,
    editingId: null,
    booksRequestId: 0
  };

  var searchTimer = null;

  function $(id) {
    return document.getElementById(id);
  }

  function create(tag, className, text) {
    var node = document.createElement(tag);
    if (className) {
      node.className = className;
    }
    if (text !== undefined) {
      node.textContent = text;
    }
    return node;
  }

  function showError(message) {
    var box = $("global-error");
    box.textContent = message;
    box.classList.remove("hidden");
  }

  function hideError() {
    var box = $("global-error");
    box.textContent = "";
    box.classList.add("hidden");
  }

  function showFormError(message) {
    var box = $("form-error");
    box.textContent = message;
    box.classList.remove("hidden");
  }

  function hideFormError() {
    var box = $("form-error");
    box.textContent = "";
    box.classList.add("hidden");
  }

  function handleApiError(error) {
    if (error && error.status === 401) {
      window.location.replace("/login");
      return true;
    }
    showError(error && error.message ? error.message : "Произошла ошибка.");
    return false;
  }

  function currentFilters() {
    var sortParts = ($("sort-filter").value || "created_at:desc").split(":");
    return {
      q: $("search-input").value.trim(),
      status: $("status-filter").value,
      genre_id: $("genre-filter").value,
      sort: sortParts[0] || "created_at",
      order: sortParts[1] || "desc"
    };
  }

  function buildQuery(params) {
    var search = new URLSearchParams();
    Object.keys(params).forEach(function (key) {
      var value = params[key];
      if (value !== "" && value !== null && value !== undefined) {
        search.append(key, value);
      }
    });
    return search.toString();
  }

  function scheduleReload() {
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(function () {
      loadBooks(true);
    }, 300);
  }

  function fillSelect(select, items, placeholder, selectedId) {
    select.replaceChildren();
    var first = create("option", null, placeholder);
    first.value = "";
    select.appendChild(first);

    items.forEach(function (item) {
      var option = create("option", null, item.name);
      option.value = String(item.id);
      select.appendChild(option);
    });

    select.value = selectedId ? String(selectedId) : "";
  }

  function renderGenreFilter() {
    fillSelect($("genre-filter"), state.genres, "Жанр", $("genre-filter").value);
  }

  async function loadReferenceData() {
    var results = await Promise.all([
      API.get("/api/genres"),
      API.get("/api/publishers"),
      API.get("/api/shelves")
    ]);

    state.genres = results[0];
    state.publishers = results[1];
    state.shelves = results[2];

    renderGenreFilter();
    fillSelect($("book-genre"), state.genres, "Без жанра", null);
    fillSelect($("book-publisher"), state.publishers, "Без издательства", null);
    fillSelect($("book-shelf"), state.shelves, "Без полки", null);
  }

  async function loadBooks(reset) {
    var requestId = ++state.booksRequestId;

    if (reset) {
      state.offset = 0;
      state.books = [];
      state.hasMore = false;
      $("books-grid").replaceChildren();
      $("books-more").classList.add("hidden");
      $("empty").classList.add("hidden");
      $("loading").classList.remove("hidden");
    }

    var filters = currentFilters();
    var params = {
      limit: PAGE_SIZE,
      offset: state.offset,
      sort: filters.sort,
      order: filters.order
    };
    if (filters.q) {
      params.q = filters.q;
    }
    if (filters.status) {
      params.status = filters.status;
    }
    if (filters.genre_id) {
      params.genre_id = filters.genre_id;
    }

    try {
      var items = await API.get("/api/books?" + buildQuery(params));
      if (requestId !== state.booksRequestId) {
        return;
      }

      state.books = reset ? items : state.books.concat(items);
      state.offset = state.books.length;
      state.hasMore = items.length === PAGE_SIZE;
      renderBooks();
    } catch (error) {
      if (requestId !== state.booksRequestId) {
        return;
      }
      $("loading").classList.add("hidden");
      $("empty").classList.add("hidden");
      handleApiError(error);
    }
  }

  function createBookCard(book) {
    var card = create("article", "book-card");
    card.dataset.id = String(book.id);

    var body = create("div", "book-body");
    body.appendChild(create("h3", "book-title", book.title));
    body.appendChild(create("p", "book-author", book.author));
    if (book.genre) {
      body.appendChild(create("p", "book-genre", book.genre.name));
    }

    var meta = create("div", "book-meta");
    meta.appendChild(
      create(
        "span",
        "status-badge status-" + book.status,
        STATUS_LABELS[book.status] || book.status
      )
    );

    if (book.rating) {
      var rating = create(
        "span",
        "book-rating",
        "★".repeat(book.rating) + "☆".repeat(5 - book.rating)
      );
      rating.title = "Оценка: " + book.rating + " из 5";
      meta.appendChild(rating);
    }

    var footer = create("div", "book-footer");

    var favoriteButton = create(
      "button",
      "book-fav" + (book.is_favorite ? " active" : ""),
      book.is_favorite ? "★" : "☆"
    );
    favoriteButton.type = "button";
    favoriteButton.title = book.is_favorite
      ? "Убрать из избранного"
      : "Добавить в избранное";
    favoriteButton.setAttribute("aria-label", favoriteButton.title);
    favoriteButton.addEventListener("click", function (event) {
      event.stopPropagation();
      toggleFavorite(book);
    });

    var actions = create("div", "book-actions");
    var editButton = create("button", "icon-btn", "✎");
    editButton.type = "button";
    editButton.title = "Редактировать";
    editButton.setAttribute("aria-label", "Редактировать книгу");
    editButton.addEventListener("click", function (event) {
      event.stopPropagation();
      openEditDialog(book);
    });

    var deleteButton = create("button", "icon-btn icon-btn-danger", "✕");
    deleteButton.type = "button";
    deleteButton.title = "Удалить";
    deleteButton.setAttribute("aria-label", "Удалить книгу");
    deleteButton.addEventListener("click", function (event) {
      event.stopPropagation();
      deleteBook(book);
    });

    actions.appendChild(editButton);
    actions.appendChild(deleteButton);
    footer.appendChild(favoriteButton);
    footer.appendChild(actions);

    card.appendChild(body);
    card.appendChild(meta);
    card.appendChild(footer);
    card.addEventListener("click", function () {
      openEditDialog(book);
    });

    return card;
  }

  function renderBooks() {
    var grid = $("books-grid");
    grid.replaceChildren();
    state.books.forEach(function (book) {
      grid.appendChild(createBookCard(book));
    });

    $("loading").classList.add("hidden");
    $("empty").classList.toggle("hidden", state.books.length !== 0);
    $("books-more").classList.toggle("hidden", !state.hasMore);
  }

  function findBook(id) {
    return (
      state.books.find(function (book) {
        return book.id === id;
      }) ||
      state.recommended.find(function (book) {
        return book.id === id;
      }) ||
      null
    );
  }

  function replaceBook(updated) {
    state.books = state.books.map(function (book) {
      return book.id === updated.id ? updated : book;
    });
    state.recommended = state.recommended.map(function (book) {
      return book.id === updated.id ? updated : book;
    });
    renderBooks();
    renderRecommended();
  }

  async function toggleFavorite(book) {
    try {
      var updated = await API.patch("/api/books/" + book.id, {
        is_favorite: !book.is_favorite
      });
      replaceBook(updated);
      await loadStats();
    } catch (error) {
      handleApiError(error);
    }
  }

  async function loadRecommended() {
    try {
      var items = await API.get(
        "/api/books?" +
          buildQuery({ sort: "rating", order: "desc", limit: 50 })
      );
      state.recommended = items.filter(function (book) {
        return (book.rating || 0) >= 4;
      });
      state.recommendedVisible = RECOMMENDED_STEP;
      renderRecommended();
    } catch (error) {
      handleApiError(error);
    }
  }

  function renderRecommended() {
    var grid = $("recommended-grid");
    grid.replaceChildren();

    state.recommended
      .slice(0, state.recommendedVisible)
      .forEach(function (book) {
        grid.appendChild(createBookCard(book));
      });

    $("recommended-empty").classList.toggle(
      "hidden",
      state.recommended.length !== 0
    );
    $("recommended-more").classList.toggle(
      "hidden",
      state.recommended.length <= state.recommendedVisible
    );
  }

  async function loadStats() {
    try {
      var stats = await API.get("/api/books/stats");
      $("stat-read").textContent = String(stats.read);
      $("stat-reading").textContent = String(stats.reading);
      $("stat-want").textContent = String(stats.want);
      $("stat-favorite").textContent = String(stats.favorites);

      var list = $("genre-stats");
      list.replaceChildren();

      if (!stats.by_genre.length) {
        list.appendChild(create("li", "genre-stats-empty", "Пока нет данных"));
        return;
      }

      stats.by_genre.forEach(function (item) {
        var row = create("li", "genre-stats-item");
        row.appendChild(create("span", "genre-stats-name", item.genre_name));
        row.appendChild(
          create("span", "genre-stats-count", String(item.count))
        );
        list.appendChild(row);
      });
    } catch (error) {
      handleApiError(error);
    }
  }

  function fillFormSelects(book) {
    fillSelect(
      $("book-genre"),
      state.genres,
      "Без жанра",
      book ? book.genre_id : null
    );
    fillSelect(
      $("book-publisher"),
      state.publishers,
      "Без издательства",
      book ? book.publisher_id : null
    );
    fillSelect(
      $("book-shelf"),
      state.shelves,
      "Без полки",
      book ? book.shelf_id : null
    );
  }

  function openCreateDialog() {
    state.editingId = null;
    $("book-form").reset();
    $("book-id").value = "";
    $("dialog-title").textContent = "Новая книга";
    $("delete-btn").classList.add("hidden");
    $("book-status").value = "want";
    $("book-rating").value = "";
    fillFormSelects(null);
    hideFormError();
    $("book-dialog").showModal();
    $("book-title").focus();
  }

  function openEditDialog(book) {
    state.editingId = book.id;
    $("book-form").reset();
    $("book-id").value = String(book.id);
    $("dialog-title").textContent = "Редактировать книгу";
    $("delete-btn").classList.remove("hidden");
    $("book-title").value = book.title;
    $("book-author").value = book.author;
    $("book-status").value = book.status;
    $("book-rating").value = book.rating ? String(book.rating) : "";
    $("book-pages").value = book.pages ? String(book.pages) : "";
    $("book-favorite").checked = Boolean(book.is_favorite);
    fillFormSelects(book);
    hideFormError();
    $("book-dialog").showModal();
    $("book-title").focus();
  }

  function closeDialog() {
    var dialog = $("book-dialog");
    if (dialog.open) {
      dialog.close();
    }
  }

  async function submitBook(event) {
    event.preventDefault();
    hideFormError();

    var title = $("book-title").value.trim();
    var author = $("book-author").value.trim();
    if (!title || !author) {
      showFormError("Заполните название и автора.");
      return;
    }

    var ratingValue = $("book-rating").value;
    var pagesValue = $("book-pages").value;
    var genreValue = $("book-genre").value;
    var publisherValue = $("book-publisher").value;
    var shelfValue = $("book-shelf").value;

    var payload = {
      title: title,
      author: author,
      status: $("book-status").value,
      rating: ratingValue ? Number(ratingValue) : null,
      pages: pagesValue ? Number(pagesValue) : null,
      is_favorite: $("book-favorite").checked,
      genre_id: genreValue ? Number(genreValue) : null,
      publisher_id: publisherValue ? Number(publisherValue) : null,
      shelf_id: shelfValue ? Number(shelfValue) : null
    };

    var saveButton = $("save-btn");
    saveButton.disabled = true;
    saveButton.textContent = "Сохранение...";

    try {
      if (state.editingId) {
        await API.patch("/api/books/" + state.editingId, payload);
      } else {
        await API.post("/api/books", payload);
      }
      closeDialog();
      await Promise.all([loadBooks(true), loadStats(), loadRecommended()]);
    } catch (error) {
      if (error.status === 401) {
        window.location.replace("/login");
        return;
      }
      showFormError(error.message);
    } finally {
      saveButton.disabled = false;
      saveButton.textContent = "Сохранить";
    }
  }

  async function deleteBook(book) {
    if (!book) {
      return;
    }
    if (!window.confirm("Удалить книгу «" + book.title + "»?")) {
      return;
    }

    try {
      await API.delete("/api/books/" + book.id);
      if (state.editingId === book.id) {
        closeDialog();
      }
      await Promise.all([loadBooks(true), loadStats(), loadRecommended()]);
    } catch (error) {
      if (error.status === 401) {
        window.location.replace("/login");
        return;
      }
      showFormError(error.message);
    }
  }

  function bindEvents() {
    $("logout-btn").addEventListener("click", async function () {
      try {
        await API.post("/api/auth/logout");
      } catch (error) {}
      window.location.replace("/login");
    });

    $("search-input").addEventListener("input", scheduleReload);
    $("genre-filter").addEventListener("change", function () {
      loadBooks(true);
    });
    $("status-filter").addEventListener("change", function () {
      loadBooks(true);
    });
    $("sort-filter").addEventListener("change", function () {
      loadBooks(true);
    });

    $("books-more").addEventListener("click", function () {
      loadBooks(false);
    });

    $("recommended-more").addEventListener("click", function () {
      state.recommendedVisible += RECOMMENDED_STEP;
      renderRecommended();
    });

    $("add-book-btn").addEventListener("click", openCreateDialog);
    $("cancel-btn").addEventListener("click", closeDialog);
    $("book-form").addEventListener("submit", submitBook);

    $("delete-btn").addEventListener("click", function () {
      deleteBook(findBook(state.editingId));
    });

    $("book-dialog").addEventListener("cancel", function () {
      hideFormError();
    });

    $("book-dialog").addEventListener("click", function (event) {
      if (event.target === $("book-dialog")) {
        closeDialog();
      }
    });
  }

  async function init() {
    try {
      state.user = await API.get("/api/auth/me");
    } catch (error) {
      if (error.status === 401) {
        window.location.replace("/login");
        return;
      }
      $("loading").classList.add("hidden");
      showError(error.message);
      return;
    }

    $("user-name").textContent = state.user.username;
    bindEvents();

    try {
      await loadReferenceData();
    } catch (error) {
      $("loading").classList.add("hidden");
      handleApiError(error);
      return;
    }

    await Promise.all([loadBooks(true), loadStats(), loadRecommended()]);
  }

  document.addEventListener("DOMContentLoaded", init);
})();
