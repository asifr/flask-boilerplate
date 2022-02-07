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


def test_db_create():
    with flask_app.app_context():
        db = flask_app.db
        db.destroy_db()
        db.create_tables()
    assert True


def test_create_admin():
    with flask_app.test_request_context():
        db = flask_app.db

        name = "New User"
        email = "email@example.com"
        password = "password"

        user = logic.create_admin_user(name, email, password)

        user = models.User.query.filter_by(email=email).first()

        assert user is not None
        assert user.role == logic.ROLE_ADMIN
        assert user.check_password(password)


def test_add_user_to_team():
    with flask_app.test_request_context():
        db = flask_app.db

        email = "email@example.com"
        user = models.User.query.filter_by(email=email).first()

        assert user is not None

        name = "Paid User"

        with db.txn() as session:
            team = models.Team(name=name, owner_id=user.id, creator_id=user.id)
            session.add(team)

        assert team.id is not None

        team = models.Team.query.filter_by(name=name).first()

        assert team is not None
        assert team.owner_id == user.id
        assert team.creator_id == user.id

        with db.txn() as session:
            member = models.TeamMember(
                status=logic.STATUS.get("active"), role=logic.ROLE_MEMBER
            )
            member.user = user
            member.team = team
            session.add(member)

        assert member.id is not None
