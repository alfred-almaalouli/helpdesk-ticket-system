const NEXT_STATUSES = {
  OPEN: ["IN_PROGRESS", "CLOSED"],
  IN_PROGRESS: ["RESOLVED", "OPEN"],
  RESOLVED: ["CLOSED", "OPEN"],
  CLOSED: [],
};

const form = document.getElementById("ticket-form");
const message = document.getElementById("form-message");
const rows = document.getElementById("ticket-rows");
const filter = document.getElementById("status-filter");

function showMessage(text, ok) {
  message.textContent = text;
  message.className = ok ? "success" : "error";
}

async function loadTickets() {
  const status = filter.value ? `?status=${filter.value}` : "";
  const response = await fetch(`/api/tickets${status}`);
  const tickets = await response.json();

  rows.innerHTML = "";
  for (const t of tickets) {
    const tr = document.createElement("tr");
    tr.dataset.testid = `ticket-${t.id}`;
    tr.innerHTML = `
      <td>${t.id}</td>
      <td data-testid="ticket-title"></td>
      <td class="prio-${t.priority}" data-testid="ticket-priority">${t.priority}</td>
      <td data-testid="ticket-status">${t.status}</td>
      <td class="${t.overdue ? "overdue" : ""}">${t.due_at.replace("T", " ").slice(0, 16)}</td>
      <td data-testid="ticket-actions"></td>`;
    tr.querySelector('[data-testid="ticket-title"]').textContent = t.title;  // no HTML injection

    const actions = tr.querySelector('[data-testid="ticket-actions"]');
    for (const next of NEXT_STATUSES[t.status]) {
      const button = document.createElement("button");
      button.className = "small";
      button.textContent = next === "OPEN" ? "Reopen" : next.replace("_", " ").toLowerCase();
      button.dataset.testid = `to-${next}`;
      button.onclick = () => changeStatus(t.id, next);
      actions.appendChild(button);
    }
    rows.appendChild(tr);
  }
  document.getElementById("empty-message").hidden = tickets.length > 0;
}

async function changeStatus(id, status) {
  await fetch(`/api/tickets/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  await loadTickets();
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const body = {
    title: document.getElementById("title").value,
    description: document.getElementById("description").value,
    priority: document.getElementById("priority").value,
  };
  const response = await fetch("/api/tickets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (response.ok) {
    showMessage(`Ticket #${data.id} created`, true);
    form.reset();
    await loadTickets();
  } else {
    showMessage(data.error, false);
  }
});

filter.addEventListener("change", loadTickets);
loadTickets();
