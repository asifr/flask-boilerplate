"""
Flask application using a modular factory pattern.
"""

from collections import namedtuple
from flask import Flask, render_template
from flask_cors import CORS
from flask_talisman import Talisman
from flask_mail import Mail

from config import current_config

__version__ = "0.1.0"

# defining URL routes
Route = namedtuple("Route", ["method", "rule", "func", "endpoint"])


def stub(method):
    """Utility function to call a class method without the `self` parameter."""

    def _stub(*args, **kwargs):
        return method(*args, **kwargs)

    return _stub


class FactoryRegistry:
    """
    Register classes that will be instantiated when the create_app function is
    called. Classes implementing an init_app method will be called with the
    flask app as an argument. Classes implementing routes property will be
    added as url rules.
    """

    def __init__(self):
        self._registry = []
        self._apps = {}

    def add(self, *args):
        self._registry.extend(args)

    def run(self, app):
        for obj in self._registry:
            name = obj.__name__
            self._apps[name] = obj()
            # if the factory has an init_app method, call it
            if hasattr(obj, "init_app"):
                self._apps[name].init_app(app)
            # if the factory has routes, add the route as a url rule
            if hasattr(self._apps[name], "routes"):
                if not isinstance(self._apps[name].routes, list):
                    raise TypeError(f"{name}.routes must be a list of Route objects")
                for route in self._apps[name].routes:
                    app.add_url_rule(
                        rule=route.rule,
                        endpoint=route.endpoint,
                        view_func=stub(getattr(self._apps[name], route.func)),
                        methods=[route.method]
                        if isinstance(route.method, str)
                        else route.method,
                    )

    def __getitem__(self, name):
        return self._apps[name]


factories = FactoryRegistry()


def create_app(factory_registry=None):
    app = Flask(__name__)
    app.config.from_object(current_config)

    app.config.update(
        {
            "FLASK_SKIP_DOTENV": True,
            "SQLALCHEMY_DATABASE_URI": current_config.DATABASE_URI,
            "FLASK_DEBUG": current_config.DEBUG,
        }
    )

    mail = Mail()
    mail.init_app(app)

    CORS(
        app,
        resources=r"*",
        origins=current_config.CORS_ORIGINS,
        supports_credentials=True,
    )
    NONE = "'none'"
    feature_policy = {
        "accelerometer": NONE,
        "camera": NONE,
        "geolocation": NONE,
        "gyroscope": NONE,
        "magnetometer": NONE,
        "microphone": NONE,
        "payment": NONE,
        "usb": NONE,
    }

    talisman = Talisman()
    talisman.init_app(
        app,
        force_https=current_config.FORCE_HTTPS,
        strict_transport_security=current_config.FORCE_HTTPS,
        feature_policy=feature_policy,
        content_security_policy=current_config.CONTENT_POLICY,
    )

    # initialize application factories
    with app.app_context():
        factories.run(app)
        if factory_registry is not None:
            factory_registry.run(app)

    @app.errorhandler(404)
    def handle_not_found(e):
        return render_template("error.html"), 404

    return app
