"""Business rules of the ticket system: status workflow, priorities and SLA."""
from datetime import datetime, timedelta

PRIORITIES = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
STATUSES = ("OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED")

# Which status changes are allowed
TRANSITIONS = {
    "OPEN": {"IN_PROGRESS", "CLOSED"},
    "IN_PROGRESS": {"OPEN", "RESOLVED"},
    "RESOLVED": {"CLOSED", "OPEN"},      # OPEN = reopen
    "CLOSED": set(),                     # final state
}

# Time to resolve a ticket (service level agreement)
SLA_HOURS = {"CRITICAL": 4, "HIGH": 24, "MEDIUM": 72, "LOW": 168}

TITLE_MIN, TITLE_MAX = 5, 100
DESCRIPTION_MAX = 2000


class ValidationError(ValueError):
    pass


class TransitionError(ValueError):
    pass


def can_transition(current, new):
    return new in TRANSITIONS.get(current, set())


def check_transition(current, new):
    if new not in STATUSES:
        raise ValidationError(f"unknown status '{new}'")
    if not can_transition(current, new):
        raise TransitionError(f"status cannot change from {current} to {new}")


def sla_due(priority, created_at):
    return created_at + timedelta(hours=SLA_HOURS[priority])


def is_overdue(ticket, now=None):
    now = now or datetime.now()
    return ticket["status"] not in ("RESOLVED", "CLOSED") and now > ticket["due_at"]


def validate_new_ticket(data):
    """Returns cleaned data or raises ValidationError with a clear message."""
    if not isinstance(data, dict):
        raise ValidationError("request body must be a JSON object")

    title = str(data.get("title", "")).strip()
    description = str(data.get("description", "")).strip()
    priority = str(data.get("priority", "MEDIUM")).strip().upper()

    if not TITLE_MIN <= len(title) <= TITLE_MAX:
        raise ValidationError(f"title must be {TITLE_MIN}-{TITLE_MAX} characters")
    if len(description) > DESCRIPTION_MAX:
        raise ValidationError(f"description must be at most {DESCRIPTION_MAX} characters")
    if priority not in PRIORITIES:
        raise ValidationError(f"priority must be one of {', '.join(PRIORITIES)}")

    return {"title": title, "description": description, "priority": priority}
