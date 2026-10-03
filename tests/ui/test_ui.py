import re

import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.ui


def create_ticket(page, title, priority="MEDIUM"):
    page.get_by_test_id("title-input").fill(title)
    page.get_by_test_id("priority-select").select_option(priority)
    page.get_by_test_id("create-button").click()


def test_empty_list_message(page):
    expect(page.get_by_test_id("empty-message")).to_be_visible()


def test_create_ticket_appears_in_table(page):
    create_ticket(page, "Printer on floor 2 is offline", "HIGH")

    expect(page.get_by_test_id("form-message")).to_have_text("Ticket #1 created")
    row = page.get_by_test_id("ticket-1")
    expect(row.get_by_test_id("ticket-title")).to_have_text("Printer on floor 2 is offline")
    expect(row.get_by_test_id("ticket-priority")).to_have_text("HIGH")
    expect(row.get_by_test_id("ticket-status")).to_have_text("OPEN")
    expect(page.get_by_test_id("title-input")).to_have_value("")


def test_validation_error_is_shown(page):
    create_ticket(page, "abc")

    expect(page.get_by_test_id("form-message")).to_have_text("title must be 5-100 characters")
    expect(page.get_by_test_id("form-message")).to_have_class(re.compile("error"))
    expect(page.get_by_test_id("empty-message")).to_be_visible()


def test_ticket_workflow_through_buttons(page):
    create_ticket(page, "Cannot log in to e-mail")
    row = page.get_by_test_id("ticket-1")

    row.get_by_test_id("to-IN_PROGRESS").click()
    expect(row.get_by_test_id("ticket-status")).to_have_text("IN_PROGRESS")

    row.get_by_test_id("to-RESOLVED").click()
    expect(row.get_by_test_id("ticket-status")).to_have_text("RESOLVED")

    row.get_by_test_id("to-CLOSED").click()
    expect(row.get_by_test_id("ticket-status")).to_have_text("CLOSED")
    expect(row.get_by_role("button")).to_have_count(0)     # closed tickets have no actions


def test_filter_by_status(page):
    create_ticket(page, "First ticket")
    expect(page.get_by_test_id("ticket-1")).to_be_visible()
    create_ticket(page, "Second ticket")
    expect(page.get_by_test_id("ticket-2")).to_be_visible()
    page.get_by_test_id("ticket-2").get_by_test_id("to-IN_PROGRESS").click()
    expect(page.get_by_test_id("ticket-2").get_by_test_id("ticket-status")).to_have_text("IN_PROGRESS")

    page.get_by_test_id("status-filter").select_option("IN_PROGRESS")

    expect(page.locator("#ticket-rows tr")).to_have_count(1)
    expect(page.get_by_test_id("ticket-2")).to_be_visible()


def test_html_in_title_is_not_executed(page):
    dialogs = []
    page.on("dialog", lambda d: (dialogs.append(d.message), d.dismiss()))

    create_ticket(page, "<img src=x onerror=alert(1)>")

    expect(page.get_by_test_id("ticket-1").get_by_test_id("ticket-title")).to_have_text("<img src=x onerror=alert(1)>")
    assert dialogs == []
