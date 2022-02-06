from flask import current_app, jsonify, render_template, g, session, redirect, url_for

import web
import models
import logic


class Database:
    def __init__(self, dsn=None):
        self.db = None
        if dsn is not None:
            self.init(dsn)

    def init(self, dsn):
        self.db = models.Database(dsn)

    def init_app(self, app):
        """
        Binds an instance of models.Database to current_app.db
        """
        self.init(app.config["DATABASE_URI"])
        app.db = self.db


class Security:
    def __init__(self):
        self.routes = [
            web.Route(
                method=["GET", "POST"],
                rule="/login",
                func="login_view",
                endpoint="security.login",
            ),
            web.Route(
                method=["GET", "POST"],
                rule="/signup",
                func="signup_view",
                endpoint="security.signup",
            ),
            web.Route(
                method=["GET", "POST"],
                rule="/logout",
                func="logout",
                endpoint="security.logout",
            ),
        ]

    def init_app(self, app):
        """
        Binds this object to current_app.security and introduces the template
        variables: current_user and is_authenticated.
        """
        app.security = self
        app.context_processor(web.stub(self.context_processor))

    def context_processor(self):
        """Template variables"""
        return dict(
            current_user=logic.get_current_user(),
            is_authenticated=self.is_authenticated,
        )

    @property
    def is_authenticated(self):
        return logic.get_current_user() is not None

    def unauthorized(self):
        return redirect(url_for("security.login"))

    def logout(self):
        logic.logout()
        return self.unauthorized()

    def login_view(self):
        form = models.LoginForm()
        return render_template("login.html", form=form)

    def signup_view(self):
        return render_template("signup.html")


class Admin:
    def __init__(self):
        self.routes = [
            web.Route(
                method=["GET"],
                rule="/admin",
                func="homepage",
                endpoint="admin.homepage",
            ),
            web.Route(
                method=["GET", "POST"],
                rule="/admin/<table>",
                func="table_view",
                endpoint="admin.table",
            ),
            web.Route(
                method=["GET", "POST"],
                rule="/admin/<table>/<pk>",
                func="edit_view",
                endpoint="admin.edit",
            ),
        ]

    @logic.login_required
    def homepage(self):
        return render_template("admin/home.html")

    @logic.login_required
    def table_view(self, table: str):
        return render_template("admin/table.html")

    @logic.login_required
    def edit_view(self, table: str, pk: str):
        return render_template("admin/edit.html")


class Frontend:
    def __init__(self):
        self.routes = [
            web.Route(method=["GET"], rule="/", func="homepage", endpoint="homepage"),
        ]

    def homepage(self):
        return render_template("home.html")


def create_app():
    # register the application factories
    web.factories.add(Database, Security, Admin, Frontend)
    # create the flask application
    app = web.create_app()
    return app
