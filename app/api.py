"""REST API for tickets."""
from flask import Blueprint, current_app, jsonify, request

from app.workflow import (PRIORITIES, STATUSES, TransitionError, ValidationError,
                          check_transition, validate_new_ticket)

api = Blueprint("api", __name__, url_prefix="/api")


def repo():
    return current_app.config["REPOSITORY"]


def to_json(ticket):
    data = dict(ticket)
    for key in ("created_at", "due_at", "updated_at"):
        data[key] = data[key].isoformat(timespec="seconds")
    return data


def error(message, status):
    return jsonify({"error": message}), status


@api.get("/health")
def health():
    return jsonify({"status": "ok"})


@api.post("/tickets")
def create_ticket():
    try:
        data = validate_new_ticket(request.get_json(silent=True))
    except ValidationError as e:
        return error(str(e), 400)
    return jsonify(to_json(repo().create(**data))), 201


@api.get("/tickets")
def list_tickets():
    status = request.args.get("status", "").upper() or None
    priority = request.args.get("priority", "").upper() or None
    if status and status not in STATUSES:
        return error(f"unknown status '{status}'", 400)
    if priority and priority not in PRIORITIES:
        return error(f"unknown priority '{priority}'", 400)
    return jsonify([to_json(t) for t in repo().list(status, priority)])


@api.get("/tickets/<int:ticket_id>")
def get_ticket(ticket_id):
    ticket = repo().get(ticket_id)
    if not ticket:
        return error("ticket not found", 404)
    return jsonify(to_json(ticket))


@api.patch("/tickets/<int:ticket_id>")
def change_status(ticket_id):
    ticket = repo().get(ticket_id)
    if not ticket:
        return error("ticket not found", 404)
    new_status = str((request.get_json(silent=True) or {}).get("status", "")).upper()
    try:
        check_transition(ticket["status"], new_status)
    except ValidationError as e:
        return error(str(e), 400)
    except TransitionError as e:
        return error(str(e), 409)
    return jsonify(to_json(repo().update_status(ticket_id, new_status)))


@api.delete("/tickets/<int:ticket_id>")
def delete_ticket(ticket_id):
    if not repo().delete(ticket_id):
        return error("ticket not found", 404)
    return "", 204
