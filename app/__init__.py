from flask import Flask

from app.api import api
from app.repository import TicketRepository


def create_app(db_path="helpdesk.db"):
    app = Flask(__name__, static_folder="static", static_url_path="")
    app.config["REPOSITORY"] = TicketRepository(db_path)
    app.register_blueprint(api)

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    return app
