/**
 * Task Manager — frontend logic
 *
 * Security rules enforced here:
 *   1. CSRF token read from <meta> and sent on every mutating request.
 *   2. All DOM writes use document.createTextNode() — never innerHTML or
 *      template literals injected into the DOM.  The browser therefore never
 *      parses user-supplied strings as HTML regardless of their content.
 *   3. Client-side validation is a UX guard only.  All real security lives
 *      on the server.
 */

(function () {
  "use strict";

  // ------------------------------------------------------------------
  // CSRF token — read once on load from the server-rendered <meta> tag
  // ------------------------------------------------------------------
  const csrfToken = (function () {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute("content") : "";
  })();

  // ------------------------------------------------------------------
  // DOM references
  // ------------------------------------------------------------------
  const form      = document.getElementById("add-form");
  const input     = document.getElementById("task-input");
  const addBtn    = document.getElementById("add-btn");
  const taskList  = document.getElementById("task-list");
  const errorMsg  = document.getElementById("error-msg");
  const emptyMsg  = document.getElementById("empty-msg");

  const MAX_TITLE = 200;

  // ------------------------------------------------------------------
  // Utility: show / hide error banner (never echoes raw user input)
  // ------------------------------------------------------------------
  function showError(message) {
    errorMsg.textContent = "";                          // clear first
    errorMsg.appendChild(document.createTextNode(message));
    errorMsg.hidden = false;
    errorMsg.setAttribute("role", "alert");
  }

  function hideError() {
    errorMsg.hidden = true;
    errorMsg.removeAttribute("role");
    errorMsg.textContent = "";
  }

  // ------------------------------------------------------------------
  // Utility: build a task <li> node entirely with DOM APIs
  // ------------------------------------------------------------------
  function buildTaskNode(task) {
    const li = document.createElement("li");
    li.dataset.id = String(task.id);
    if (task.done) {
      li.classList.add("done");
    }

    // Title span — createTextNode prevents any HTML in the title from executing
    const titleSpan = document.createElement("span");
    titleSpan.classList.add("task-title");
    titleSpan.appendChild(document.createTextNode(task.title));

    // "Done" button
    const doneBtn = document.createElement("button");
    doneBtn.classList.add("btn-done");
    doneBtn.appendChild(document.createTextNode(task.done ? "Done" : "Mark done"));
    doneBtn.disabled = task.done;
    doneBtn.setAttribute("aria-label", "Mark task as done");
    doneBtn.addEventListener("click", function () {
      handleMarkDone(task.id, li, doneBtn);
    });

    // "Delete" button
    const deleteBtn = document.createElement("button");
    deleteBtn.classList.add("btn-delete");
    deleteBtn.appendChild(document.createTextNode("Delete"));
    deleteBtn.setAttribute("aria-label", "Delete task");
    deleteBtn.addEventListener("click", function () {
      handleDelete(task.id, li);
    });

    li.appendChild(titleSpan);
    li.appendChild(doneBtn);
    li.appendChild(deleteBtn);
    return li;
  }

  // ------------------------------------------------------------------
  // Render task list
  // ------------------------------------------------------------------
  function renderTasks(tasks) {
    // Remove all existing children safely
    while (taskList.firstChild) {
      taskList.removeChild(taskList.firstChild);
    }

    if (!tasks || tasks.length === 0) {
      emptyMsg.hidden = false;
      return;
    }
    emptyMsg.hidden = true;

    tasks.forEach(function (task) {
      taskList.appendChild(buildTaskNode(task));
    });
  }

  // ------------------------------------------------------------------
  // API helpers
  // ------------------------------------------------------------------
  function apiFetch(url, options) {
    options = options || {};
    options.headers = Object.assign({}, options.headers, {
      "X-CSRFToken": csrfToken,
    });
    return fetch(url, options).then(function (res) {
      // Parse JSON regardless of status so we can read the error message
      return res.json().then(function (body) {
        return { status: res.status, body: body };
      });
    });
  }

  function loadTasks() {
    apiFetch("/tasks").then(function (result) {
      if (result.status === 200) {
        renderTasks(result.body.tasks);
      } else {
        showError("Could not load tasks.");
      }
    }).catch(function () {
      showError("Network error. Please refresh.");
    });
  }

  // ------------------------------------------------------------------
  // Handle: add task
  // ------------------------------------------------------------------
  form.addEventListener("submit", function (event) {
    event.preventDefault();
    hideError();

    const raw = input.value;

    // Client-side UX guards (not security — server validates too)
    const trimmed = raw.trim();
    if (trimmed.length === 0) {
      showError("Title cannot be empty.");
      input.focus();
      return;
    }
    if (trimmed.length > MAX_TITLE) {
      showError("Title must be " + MAX_TITLE + " characters or fewer.");
      input.focus();
      return;
    }

    addBtn.disabled = true;

    apiFetch("/tasks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: trimmed }),
    }).then(function (result) {
      if (result.status === 201) {
        input.value = "";
        loadTasks();
      } else if (result.status === 429) {
        handleRateLimit();
      } else {
        // Show the server's validation message (safe — it comes from our own code)
        showError(result.body.error || "Could not add task.");
      }
    }).catch(function () {
      showError("Network error.");
    }).finally(function () {
      addBtn.disabled = false;
    });
  });

  // ------------------------------------------------------------------
  // Handle: mark done
  // ------------------------------------------------------------------
  function handleMarkDone(taskId, li, btn) {
    btn.disabled = true;

    apiFetch("/tasks/" + taskId + "/done", { method: "PATCH" })
      .then(function (result) {
        if (result.status === 200) {
          li.classList.add("done");
          btn.textContent = "";
          btn.appendChild(document.createTextNode("Done"));
        } else {
          btn.disabled = false;
          showError("Could not mark task as done.");
        }
      })
      .catch(function () {
        btn.disabled = false;
        showError("Network error.");
      });
  }

  // ------------------------------------------------------------------
  // Handle: delete task
  // ------------------------------------------------------------------
  function handleDelete(taskId, li) {
    apiFetch("/tasks/" + taskId, { method: "DELETE" })
      .then(function (result) {
        if (result.status === 200) {
          taskList.removeChild(li);
          if (taskList.children.length === 0) {
            emptyMsg.hidden = false;
          }
        } else {
          showError("Could not delete task.");
        }
      })
      .catch(function () {
        showError("Network error.");
      });
  }

  // ------------------------------------------------------------------
  // Handle: rate limit — disable form with countdown
  // ------------------------------------------------------------------
  function handleRateLimit() {
    const WAIT = 30;
    addBtn.disabled = true;
    input.disabled = true;
    let remaining = WAIT;

    showError("Too many requests. Please wait " + remaining + " seconds.");

    const interval = setInterval(function () {
      remaining -= 1;
      if (remaining <= 0) {
        clearInterval(interval);
        addBtn.disabled = false;
        input.disabled = false;
        hideError();
      } else {
        showError("Too many requests. Please wait " + remaining + " seconds.");
      }
    }, 1000);
  }

  // ------------------------------------------------------------------
  // Initial load
  // ------------------------------------------------------------------
  loadTasks();
})();
