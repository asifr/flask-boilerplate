# Flask app boilerplate

Action | Command
--- | ---
Start Gunicorn server | `python manage.py start-server`
Stop a running Gunicorn server | `python manage.py stop-server`

## Layout

File | Description
--- | ---
`config.py` | Development and production config options
`web.py` | Flask application setup
`models.py` | ORM models and forms
`logic.py` | Business logic
`app.py` | Application factories for views and the main wsgi entrypoint
`manage.py` | Command line interface
`test.py` | Unit tests

## Notes

Starting the gunicorn server with `start-server` writes a pid file to the `./logs` folder. The `stop-server` command loads this pid file and sends a TERM signal to kill the process.

Add the `@logic.login_required` decorator to view functions to check user authentication status.