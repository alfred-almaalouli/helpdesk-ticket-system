import threading

import pytest
from werkzeug.serving import make_server

from app import create_app


@pytest.fixture
def app(tmp_path):
    return create_app(str(tmp_path / "test.db"))


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def live_server(app):
    """Runs the real app on a free local port for the UI tests."""
    server = make_server("127.0.0.1", 0, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


@pytest.fixture(scope="session")
def browser():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture
def page(browser, live_server):
    context = browser.new_context()
    page = context.new_page()
    page.goto(live_server)
    yield page
    context.close()
