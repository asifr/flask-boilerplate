"""
Unit tests for flask app.

Flask contexts:
    with flask_app.app_context() as ctx:
    with flask_app.test_client() as client:
    with flask_app.test_request_context():
"""
import web
import app
import models
import logic
from config import current_config

import importlib

importlib.reload(web)
importlib.reload(app)
importlib.reload(models)
importlib.reload(logic)

flask_app = app.create_app()


def test_db_connect():
    with flask_app.test_request_context():
        con = flask_app.db


def test_create_user():
    with flask_app.test_request_context():
        db = flask_app.db

        user = models.User(name="User name", email="email@provider.com", role="admin")
        user.set_password("password")

        try:
            db.session.add(user)
            db.session.commit()
        except:
            db.session.rollback()
