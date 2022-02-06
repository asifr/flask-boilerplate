"""
Models and forms.
"""

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from flask_wtf import FlaskForm
from wtforms_alchemy import ModelForm
from wtforms import validators, StringField, PasswordField, HiddenField, SubmitField

Base = declarative_base()


class classproperty(object):
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


class Model(Base):
    __abstract__ = True

    created = sa.Column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    deleted = sa.Column(sa.Boolean(), default=False)

    @classmethod
    def set_session(cls, session):
        """
        Call this method after establishing a database connection and before
        creating models as Model.set_session(session)
        """
        cls._session = session

    @classproperty
    def session(cls):
        """Get the bound session"""
        return cls._session

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def delete(self, force=False):
        """Soft delete.

        Args:
            forced (bool): hard delete, default=False
        """
        if force:
            self.session.delete(self)
            return self.session.commit()
        self.deleted = True
        return self.session.commit()


class User(Model):
    """
    User

    Usage:
        user.memberships -> [<TeamMember>, ...]
    """

    __tablename__ = "user"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    name = sa.Column(sa.String, nullable=True)
    email = sa.Column(sa.String, index=True, unique=True, nullable=False)
    password_hash = sa.Column(sa.String, nullable=False)
    status = sa.Column(sa.SmallInteger, default=1, nullable=False)
    role = sa.Column(sa.String, default="user", nullable=False)
    login_token = sa.Column(sa.String, unique=True, index=True, nullable=True)

    def set_password(self, password):
        from werkzeug.security import generate_password_hash

        self.password_hash = generate_password_hash(password)

    def check_password(self, value):
        from werkzeug.security import check_password_hash

        return check_password_hash(self.password, value)


class Team(Model):
    """
    A team is a collection of users sharing the same resources. All users get
    a team. Some teams have more than one member. Most resources in the
    application should belong to a team.

    Usage:
        team.members -> [<TeamMember>, ...]
    """

    __tablename__ = "team"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    name = sa.Column(sa.Unicode(255), nullable=False)
    creator_id = sa.Column(sa.ForeignKey("user.id"), index=True, nullable=False)
    owner_id = sa.Column(sa.ForeignKey("user.id"), nullable=False)

    creator = relationship("User", foreign_keys=[creator_id])
    owner = relationship("User", foreign_keys=[owner_id])

    def has_member(self, user):
        return user in [member.user for member in self.active_members]


class TeamMember(Model):
    __tablename__ = "team_member"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    team_id = sa.Column(sa.ForeignKey("team.id"), index=True, nullable=False)
    user_id = sa.Column(sa.ForeignKey("user.id"), index=True, nullable=True)
    status = sa.Column(sa.SmallInteger, default=1, nullable=False)
    role = sa.Column(sa.String, default="member", nullable=False)

    # Team.members and User.memberships
    team = relationship("Team", backref="members", lazy="joined")
    user = relationship("User", foreign_keys=[user_id], backref="memberships")


class Database:
    """
    Establishes a connection to the database and initializes the models.
    Also provides utility functions to modify database tables.
    """

    def __init__(self, dsn=None):
        self.dsn = dsn
        self.engine = None
        self.session = None
        self.meta = None
        if self.dsn is not None:
            self.connect(self.dsn)

    def connect(self, dsn):
        self.engine = create_engine(dsn)
        Session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.session = Session()
        self.meta = sa.MetaData()
        self.reflect()
        Model.set_session(self.session)

    def reflect(self):
        self.meta.reflect(bind=self.engine)
        self.session.flush()

    def create_tables(self):
        """Create all tables"""
        self.reflect()
        Base.metadata.create_all(bind=self.engine)
        self.reflect()

    def destroy_db(self):
        self.meta.bind = self.engine
        self.meta.reflect()
        tables = list(self.meta.sorted_tables)
        while len(tables):
            for table in tables:
                try:
                    table.drop(checkfirst=True)
                    tables.remove(table)
                except InternalError:
                    pass


class UserForm(ModelForm):
    class Meta:
        model = User
        exclude = ["password_hash"]


class TeamForm(ModelForm):
    class Meta:
        model = Team


class LoginForm(FlaskForm):
    email = StringField(
        "Email", validators=[validators.email(), validators.InputRequired()]
    )
    password = PasswordField("Password", validators=[validators.InputRequired()])
    submit = SubmitField("Login")

    def validate(self):
        check_validate = super(LoginForm, self).validate()

        # if our field validators do not pass
        if not check_validate:
            return False

        # Does the user exist?
        user = User.query.filter_by(email=self.email.data).first()
        if not user:
            self.email.errors.append("Invalid email or password")
            return False

        # Do the passwords match
        if not user.check_password(self.password.data):
            self.email.errors.append("Invalid email or password")
            return False

        return True


class ChangePasswordForm(FlaskForm):
    password = PasswordField(
        "Password",
        validators=[
            validators.InputRequired(),
            validators.length(min=4),
            validators.EqualTo("confirm", message="Passwords must match"),
        ],
    )
    confirm = PasswordField("Repeat Password")


class RequestPasswordResetForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[validators.email(), validators.InputRequired()],
        description="Enter the email you used to signup",
    )
