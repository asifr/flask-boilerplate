from functools import wraps
from flask import current_app, g, session, request, url_for

import models

STATUS = {"blocked": 0, "active": 1}
ROLE_ADMIN = "admin"
ROLE_USER = "user"
ROLE_MEMBER = "member"


def login_required(func):
    """
    If you decorate a view with this, it will ensure that the current user is
    logged in and authenticated before calling the actual view. (If they are
    not, it calls the :attr:`LoginManager.unauthorized` callback.) For
    example::
        @app.route('/post')
        @login_required
        def post():
            pass
    If there are only certain times you need to require that your user is
    logged in, you can do so with::
        if not current_user.is_authenticated:
            return current_app.security.unauthorized()
    which is essentially the code that this function adds to your views.
    It can be convenient to globally turn off authentication when unit testing.
    To enable this, if the application configuration variable `LOGIN_DISABLED`
    is set to `True`, this decorator will be ignored.
    """

    @wraps(func)
    def decorated_view(*args, **kwargs):
        if request.method in set(["OPTIONS"]):
            return func(*args, **kwargs)
        elif current_app.config.get("LOGIN_DISABLED", False):
            return func(*args, **kwargs)
        elif not current_app.security.is_authenticated:
            return current_app.security.unauthorized()
        return func(*args, **kwargs)

    return decorated_view


def get_current_user():
    if hasattr(g, "user"):
        if g.user is not None:
            return g.user

    # Load user from Flask Session
    user_token = session.get("_user_token")
    if user_token is not None:
        g.user = models.User.get_by(login_token=user_token)
        # status==0 is an inactive user account (blocked)
        if g.user.status == STATUS["blocked"]:
            session["_user_token"] = None
            return None
        return g.user


def email_is_available(email: str):
    """Check if an email is available."""
    if email is None:
        return False
    return models.User.query.filter_by(email=email).first() is None


def create_user(name: str, email: str, password: str, role: str, status: int):
    """Create a user. Returns the user object."""
    if email_is_available(email):
        db = current_app.db

        with db.txn() as session:
            user = models.User(name=name, email=email, role=role, status=int(status))
            user.set_password(password)
            session.add(user)

        return user


def create_admin_user(name, email, password):
    return create_user(name, email, password, ROLE_ADMIN, STATUS.get("active"))


def logout():
    """Remove the user from a session and the global variable"""
    if "_user_token" in session:
        session.pop("_user_token")
    g.user = None
