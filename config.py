import os
from pathlib import Path

APP_DIR = Path(os.path.abspath(os.path.dirname(__file__)))


class Config:
    # app
    APPNAME = "app"
    UI_HOST = "0.0.0.0"
    UI_PORT = "5000"
    CONTENT_DIR = APP_DIR / "content/"
    LOGS_DIR = APP_DIR / "logs/"
    TEMPLATES_FOLDER = "templates"

    # Generate secret key: openssl rand -base64 32
    SECRET_KEY = os.environ.get("SECRET_KEY", b"secret")

    # Gunicorn WSGI application settings
    # From: https://docs.gunicorn.org/en/latest/run.html
    # WSGI_APP is of the pattern $(MODULE_NAME):$(VARIABLE_NAME).
    # The module name can be a full dotted path. The variable name refers to a
    # WSGI callable that should be found in the specified module.
    WSGI_APP = "app:create_app()"
    GUNICORN_THREADS = 1

    # flask
    TEMPLATES_AUTO_RELOAD = True
    FLASK_ENV = "development"
    DEBUG = True
    PROFILE = True
    MAINTENANCE = False

    # aws
    AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

    # stripe
    STRIPE_PUB_KEY = os.environ.get("STRIPE_PUB_KEY")
    STRIPE_SEC_KEY = os.environ.get("STRIPE_SEC_KEY")
    STRIPE_ENDPOINT_KEY = os.environ.get("STRIPE_ENDPOINT_KEY")

    # flask-mail using sendgrid
    MAIL_SERVER = "smtp.sendgrid.net"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("SENDGRID_API_KEY")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")

    # celery
    BROKER_DB_NAME = "celery.db"
    CELERY_RESULT_DB_NAME = "celeryresults.db"
    CELERY_BROKER_URL = "redis://localhost:6379/0"

    # session
    FORCE_HTTPS = True
    PREFERRED_URL_SCHEME = "http"
    CONTENT_POLICY = "default-src: 'self' 'unsafe-inline' 'unsafe-eval' data: *"
    CORS_ORIGINS = ["*"]
    SESSION_EXPIRE = 43200
    LOGIN_DISABLED = False

    # database
    SQLALCHEMY_ECHO = True
    DB_NAME = "app.db"


class DevelopmentConfig(Config):
    FLASK_ENV = "development"


class ProductionConfig(Config):
    FLASK_ENV = "production"
    DEBUG = False
    PROFILE = False
    MAINTENANCE = False
    SQLALCHEMY_ECHO = False


configs = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}

current_config = configs.get(os.environ.get("CONFIG", "development"))

# create the content folder
current_config.CONTENT_DIR.mkdir(parents=True, exist_ok=True)

# create the logs folder
current_config.LOGS_DIR.mkdir(parents=True, exist_ok=True)

# sqlite db file
current_config.DATABASE_URI = "sqlite:///" + str(
    current_config.CONTENT_DIR / current_config.DB_NAME
)

# gunicorn PID file
current_config.GUNICORN_PID_FILE = current_config.LOGS_DIR / (
    current_config.APPNAME + "-gunicorn.pid"
)

# supervisor PID file: this path must match the pidfile in the supervisor config
current_config.SUPERVISOR_PID_FILE = current_config.LOGS_DIR / "supervisord.pid"

# full path to celery sqlite db files
# current_config.CELERY_BROKER_URL = "sqla+sqlite:///" + str(current_config.CONTENT_DIR / current_config.BROKER_DB_NAME)
# current_config.CELERY_RESULT_BACKEND = "db+sqlite:///" + str(current_config.CONTENT_DIR / current_config.CELERY_RESULT_DB_NAME)
