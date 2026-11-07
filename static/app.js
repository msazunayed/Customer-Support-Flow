const $ = (selector) => document.querySelector(selector);

const SAMPLES = [
  { name: "SJ. Zahidul", issue: "Unable to access premium features after payment" },
  { name: "Md. Ifran", issue: "I was charged twice for my monthly subscription this month" },
  { name: "Aabid hasan", issue: "The app crashes every time I try to upload a PDF file" },
  { name: "Sajib khan", issue: "Please add dark mode and keyboard shortcuts to the dashboard" },
  { name: "Shakil Ahmed", issue: "I'm locked out of my account and the password reset email never arrives" },
];

const STAR_SVG = `<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 17.27 18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/></svg>`;

let activeTicket = null;

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value ?? "";
  return div.innerHTML;
}

function categoryClass(category) {
  return "cat-" + String(category).toLowerCase().replace(/ /g, "_");
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Something went wrong");
  }
  return data;
}

async function checkHealth() {
  const badge = $("#engine-badge");
  const text = badge.querySelector(".status-text");
  try {
    await api("/api/health");
    badge.classList.add("live");
    text.textContent = "Connected";
  } catch {
    text.textContent = "Server unreachable";
  }
}

function renderSamples() {
  const list = $("#sample-list");
  SAMPLES.forEach((sample) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = sample.issue;
    button.addEventListener("click", () => {
      $("#customer_name").value = sample.name;
      $("#issue_description").value = sample.issue;
    });
    list.appendChild(button);
  });
}

function animatePipeline() {
  document.querySelectorAll(".step").forEach((step) => {
    step.style.animation = "none";
    void step.offsetWidth;
    step.style.animation = "";
  });
}

function renderTrace(history) {
  $("#r-history").innerHTML = history.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function renderStars(score) {
  const container = $("#stars");
  container.innerHTML = "";
  for (let i = 1; i <= 5; i++) {
    const star = document.createElement("button");
    star.type = "button";
    star.innerHTML = STAR_SVG;
    star.setAttribute("aria-label", `${i} star${i > 1 ? "s" : ""}`);
    if (i <= score) star.classList.add("on");
    star.addEventListener("click", () => submitFeedback(i));
    container.appendChild(star);
  }
}

function renderTicket(ticket) {
  activeTicket = ticket;
  $("#empty-state").classList.add("hidden");
  const result = $("#result");
  result.classList.remove("hidden");
  result.classList.remove("fade-in");
  void result.offsetWidth;
  result.classList.add("fade-in");

  $("#r-ticket").textContent = ticket.ticket_id;
  $("#r-customer").textContent = ticket.customer_name;
  $("#r-issue").textContent = ticket.issue_description;
  $("#r-resolution").textContent = ticket.resolution || "Pending";

  const priority = $("#r-priority");
  priority.textContent = `${ticket.priority} priority`;
  priority.className = `pill ${ticket.priority}`;

  const category = $("#r-category");
  category.textContent = ticket.category;
  category.className = `pill ${categoryClass(ticket.category)}`;

  renderTrace(ticket.history || []);
  renderStars(ticket.satisfaction_score || 0);
  $("#feedback-msg").textContent = ticket.satisfaction_score ? "Thanks for your rating." : "";
  animatePipeline();
}

async function submitFeedback(score) {
  if (!activeTicket) return;
  try {
    const updated = await api(`/api/tickets/${activeTicket.ticket_id}/feedback`, {
      method: "POST",
      body: JSON.stringify({ score }),
    });
    activeTicket = updated;
    renderStars(score);
    $("#feedback-msg").textContent = "Thanks for your rating.";
    loadTickets();
  } catch (err) {
    $("#feedback-msg").textContent = err.message;
  }
}

function showError(message) {
  const error = $("#form-error");
  error.textContent = message;
  error.classList.remove("hidden");
}

async function handleSubmit(event) {
  event.preventDefault();
  const name = $("#customer_name").value.trim();
  const issue = $("#issue_description").value.trim();
  $("#form-error").classList.add("hidden");

  if (!name) return showError("Please enter the customer name.");
  if (issue.length < 5) return showError("Please describe the issue in a few words.");

  const button = $("#submit-btn");
  button.disabled = true;
  button.classList.add("loading");
  button.querySelector(".btn-text").textContent = "Running flow...";

  try {
    const ticket = await api("/api/tickets", {
      method: "POST",
      body: JSON.stringify({ customer_name: name, issue_description: issue }),
    });
    renderTicket(ticket);
    loadTickets();
  } catch (err) {
    showError(err.message);
  } finally {
    button.disabled = false;
    button.classList.remove("loading");
    button.querySelector(".btn-text").textContent = "Run flow";
  }
}

async function loadTickets() {
  const container = $("#tickets-list");
  try {
    const tickets = await api("/api/tickets");
    if (!tickets.length) {
      container.innerHTML = `<p class="muted">No tickets processed yet.</p>`;
      return;
    }
    container.innerHTML = "";
    tickets.forEach((ticket) => {
      const card = document.createElement("button");
      card.type = "button";
      card.className = "ticket-card";
      card.innerHTML = `
        <span class="ticket-id">${escapeHtml(ticket.ticket_id)}</span>
        <strong>${escapeHtml(ticket.customer_name)}</strong>
        <span class="pill ${categoryClass(ticket.category)}">${escapeHtml(ticket.category)}</span>
        <p>${escapeHtml(ticket.issue_description)}</p>`;
      card.addEventListener("click", () => renderTicket(ticket));
      container.appendChild(card);
    });
  } catch (err) {
    container.innerHTML = `<p class="error">${escapeHtml(err.message)}</p>`;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  renderSamples();
  checkHealth();
  loadTickets();
  $("#ticket-form").addEventListener("submit", handleSubmit);
  $("#refresh").addEventListener("click", loadTickets);
});
