from flask import current_app, jsonify, render_template

import web
import sqlutils


class Database:
    def __init__(self, dburi=None):
        self.con = None
        if dburi is not None:
            self.init(dburi)

    def init(self, dburi):
        self.con = sqlutils.connect(dburi)
        sqlutils.enable_wal(self.con)

    def init_app(self, app):
        self.init(app.config["DATABASE_URI"])
        app.db = self


class Frontend:
    def __init__(self):
        self.routes = [
            web.Route(method=["GET"], rule="/", func="homepage", endpoint="homepage"),
        ]

    def homepage(self):
        con = current_app.db.con
        return render_template("home.html")


def create_app():
    # register the application factories
    web.factories.add(
        Database,
        Frontend
    )
    # create the flask application
    app = web.create_app()
    return app