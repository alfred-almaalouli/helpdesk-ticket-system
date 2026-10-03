from datetime import datetime, timedelta

import pytest

from app.workflow import (STATUSES, TRANSITIONS, TransitionError, ValidationError,
                          can_transition, check_transition, is_overdue, sla_due,
                          validate_new_ticket)

pytestmark = pytest.mark.unit

NOW = datetime(2026, 10, 1, 9, 0, 0)


# --- state transition testing: every combination of current and new status ---

ALLOWED = {
    ("OPEN", "IN_PROGRESS"), ("OPEN", "CLOSED"),
    ("IN_PROGRESS", "OPEN"), ("IN_PROGRESS", "RESOLVED"),
    ("RESOLVED", "CLOSED"), ("RESOLVED", "OPEN"),
}


@pytest.mark.parametrize("current", STATUSES)
@pytest.mark.parametrize("new", STATUSES)
def test_transition_table(current, new):
    assert can_transition(current, new) == ((current, new) in ALLOWED)


def test_closed_is_a_final_state():
    assert TRANSITIONS["CLOSED"] == set()
    with pytest.raises(TransitionError):
        check_transition("CLOSED", "OPEN")


def test_unknown_status_is_a_validation_error():
    with pytest.raises(ValidationError):
        check_transition("OPEN", "DONE")


# --- SLA and overdue (boundary values) ---

@pytest.mark.parametrize("priority, hours", [("CRITICAL", 4), ("HIGH", 24), ("MEDIUM", 72), ("LOW", 168)])
def test_sla_per_priority(priority, hours):
    assert sla_due(priority, NOW) == NOW + timedelta(hours=hours)


@pytest.mark.parametrize("now, overdue", [
    (NOW + timedelta(hours=4) - timedelta(seconds=1), False),
    (NOW + timedelta(hours=4), False),                       # exactly on the deadline
    (NOW + timedelta(hours=4) + timedelta(seconds=1), True),
])
def test_overdue_boundary(now, overdue):
    ticket = {"status": "OPEN", "due_at": sla_due("CRITICAL", NOW)}
    assert is_overdue(ticket, now) is overdue


@pytest.mark.parametrize("status", ["RESOLVED", "CLOSED"])
def test_finished_tickets_are_never_overdue(status):
    ticket = {"status": status, "due_at": NOW}
    assert is_overdue(ticket, NOW + timedelta(days=30)) is False


# --- input validation (equivalence partitioning + boundary values) ---

@pytest.mark.parametrize("length, valid", [(4, False), (5, True), (100, True), (101, False)])
def test_title_length_boundaries(length, valid):
    data = {"title": "x" * length, "priority": "LOW"}
    if valid:
        assert validate_new_ticket(data)["title"] == "x" * length
    else:
        with pytest.raises(ValidationError):
            validate_new_ticket(data)


def test_title_with_only_spaces_is_rejected():
    with pytest.raises(ValidationError):
        validate_new_ticket({"title": "        ", "priority": "LOW"})


def test_input_is_trimmed_and_priority_is_case_insensitive():
    data = validate_new_ticket({"title": "  Printer broken  ", "priority": " high "})
    assert data == {"title": "Printer broken", "description": "", "priority": "HIGH"}


def test_default_priority_is_medium():
    assert validate_new_ticket({"title": "VPN not working"})["priority"] == "MEDIUM"


@pytest.mark.parametrize("data", [
    {"title": "Valid title", "priority": "URGENT"},
    {"title": "Valid title", "description": "x" * 2001},
    None,
    ["not", "an", "object"],
])
def test_invalid_input_is_rejected(data):
    with pytest.raises(ValidationError):
        validate_new_ticket(data)


def test_description_at_maximum_length_is_accepted():
    assert len(validate_new_ticket({"title": "Valid title", "description": "x" * 2000})["description"]) == 2000
