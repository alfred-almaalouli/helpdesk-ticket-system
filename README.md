# Helpdesk Ticket System – built and tested end to end

![CI](https://github.com/alfred-almaalouli/helpdesk-ticket-system/actions/workflows/ci.yml/badge.svg)

A small helpdesk application where support tickets are created, prioritised and moved through a workflow – and a **complete test pyramid** around it: unit tests, API tests and browser tests, plus a Docker smoke test, all running in a CI pipeline.

I built the application myself so that I could test it the way a tester works in a real team: from the business rules down to the user interface.

## The application

- Create tickets with title, description and priority (Low / Medium / High / Critical)
- Every priority has an **SLA** (time to resolve): Critical 4 h, High 24 h, Medium 72 h, Low 168 h – overdue tickets are highlighted
- Status workflow – only these changes are allowed (everything else returns **409 Conflict**):

| From | To |
|------|----|
| OPEN | IN_PROGRESS, CLOSED |
| IN_PROGRESS | RESOLVED, OPEN |
| RESOLVED | CLOSED, OPEN (reopen) |
| CLOSED | – (final state) |

- REST API (Flask) + simple web interface (HTML/JavaScript) + SQLite database

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | health check |
| POST | `/api/tickets` | create ticket (400 on invalid data) |
| GET | `/api/tickets?status=&priority=` | list and filter tickets |
| GET | `/api/tickets/{id}` | one ticket (404 if missing) |
| PATCH | `/api/tickets/{id}` | change status (409 if the transition is not allowed) |
| DELETE | `/api/tickets/{id}` | delete ticket |

## Test pyramid

| Level | What | Tool | Tests |
|-------|------|------|-------|
| **Unit** | workflow rules, SLA, input validation | pytest | 39 |
| **API** | all endpoints, status codes, filters, full lifecycle | pytest + Flask test client | 15 |
| **UI** | create ticket, validation message, workflow buttons, filter, XSS check | Playwright | 6 |
| **Smoke** | Docker image starts and API answers | GitHub Actions + curl | 1 |

Test design techniques (ISTQB):

- **State transition testing** – all 16 combinations of current and new status are tested (6 allowed, 10 forbidden)
- **Boundary value analysis** – title length 4 / 5 / 100 / 101 characters, description 2000 / 2001, overdue exactly at the deadline ± 1 second
- **Equivalence partitioning** – valid and invalid priorities, statuses and request bodies
- **Security check** – HTML in a ticket title is shown as text and not executed

## CI pipeline

```
Unit + API tests (with coverage) ──► UI tests (Playwright) ──► Docker build + smoke test
```

Each stage only runs when the previous one is green.

## Run it

```bash
pip install -r requirements-dev.txt
python run.py                      # http://localhost:5000

pytest -m unit                     # fast business rule tests
pytest -m api
python -m playwright install chromium
pytest -m ui                       # browser tests
pytest --cov=app                   # everything with coverage

docker build -t helpdesk . && docker run -p 5000:5000 helpdesk
```

## Project structure

```
app/
  workflow.py      business rules: transitions, SLA, validation
  repository.py    SQLite storage
  api.py           REST API
  static/          web interface (HTML, CSS, JavaScript)
tests/
  unit/            pytest unit tests
  api/             API tests
  ui/              Playwright browser tests
Dockerfile
.github/workflows/ci.yml
```

## Tech stack

Python · Flask · SQLite · JavaScript · pytest · Playwright · Docker · GitHub Actions

## Author

Alfred Al Maalouli – [GitHub](https://github.com/alfred-almaalouli)
