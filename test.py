"""
Unit tests for flask app.

Flask contexts:
    with flask_app.app_context() as ctx:
    with flask_app.test_client() as client:
    with flask_app.test_request_context():
"""
import web
import app
import sqlutils
from config import current_config

import importlib

importlib.reload(web)
importlib.reload(app)
importlib.reload(sqlutils)

flask_app = app.create_app()


def test_db_connect():
    with flask_app.test_request_context():
        con = flask_app.db.con
