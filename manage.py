#!/usr/bin/env python
import os
import subprocess
from pathlib import Path
import click

from config import current_config


class ShellCommandException(Exception):
    pass


def exec_cmd(
    cmd,
    throw_on_error=True,
    env=None,
    stream_output=False,
    cwd=None,
    cmd_stdin=None,
    **kwargs,
):
    """Runs a command as a child process.
    A convenience wrapper for running a command from a Python script.

    Parameters
    ----------
    cmd : List[str]
        the command to run, as a list of strings
    throw_on_error : bool
        if true, raises an Exception if the exit code of the program is nonzero
    env : Dict[str,str]
        additional environment variables to be defined when running the
        child process
    cwd : str
        working directory for child process
    stream_output : bool
        if true, does not capture standard output and error; if false, captures
        these streams and returns them
    cmd_stdin : str
        if specified, passes the specified string as stdin to the child process

    Notes
    -----
    Note on the return value: If stream_output is true, then only the exit code
    is returned. If stream_output is false, then a tuple of the exit code,
    standard output and standard error is returned.
    """
    cmd_env = os.environ.copy()
    if env:
        cmd_env.update(env)
    if stream_output:
        child = subprocess.Popen(
            cmd,
            env=cmd_env,
            cwd=cwd,
            universal_newlines=True,
            stdin=subprocess.PIPE,
            **kwargs,
        )
        child.communicate(cmd_stdin)
        exit_code = child.wait()
        if throw_on_error and exit_code != 0:
            raise ShellCommandException("Non-zero exitcode: %s" % (exit_code))
        return exit_code
    else:
        child = subprocess.Popen(
            cmd,
            env=cmd_env,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            universal_newlines=True,
            **kwargs,
        )
        (stdout, stderr) = child.communicate(cmd_stdin)
        exit_code = child.wait()
        if throw_on_error and exit_code != 0:
            raise ShellCommandException(
                "Non-zero exit code: %s\n\nSTDOUT:\n%s\n\nSTDERR:%s"
                % (exit_code, stdout, stderr)
            )
        return exit_code, stdout, stderr


def get_pid_from_file(file):
    if file.is_file():
        with open(file) as f:
            return int(f.readline().rstrip())
    return None


def build_uvicorn_command(host, port, num_workers, mode="development"):
    """Use uvicorn to start the web server"""
    cmd = [
        "uvicorn",
        "--host",
        host,
        "--port",
        "%s" % port,
        "--workers",
        "%s" % num_workers,
    ]
    if mode == "production":
        cmd += ["--log-level", "error"]
    else:
        cmd += [
            "--reload",
            "--reload-dir",
            str(current_config.APP_DIR),
            "--log-level",
            "debug",
        ]
    cmd += [current_config.WSGI_APP]
    return cmd


def build_gunicorn_command(host, port, threads, mode="development"):
    """Use gunicorn to start the web server"""
    cmd = ["gunicorn", "-b", f"{host}:{port}", "--threads", "%s" % threads]
    if mode == "production":
        cmd += ["--log-level", "error"]
    else:
        cmd += [
            "--reload",
            "--log-level",
            "debug",
            "-p",
            current_config.GUNICORN_PID_FILE,
        ]
    cmd += [current_config.WSGI_APP, "& disown"]
    return cmd


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "-m", "--mode", help="production or development", default=current_config.FLASK_ENV
)
@click.option(
    "-t", "--threads", help="Number of threads", default=current_config.GUNICORN_THREADS
)
def start_server(mode, threads):
    """Start the gunicorn server"""
    server_cmd = build_gunicorn_command(
        current_config.UI_HOST, port=current_config.UI_PORT, threads=threads, mode=mode
    )
    exec_cmd(server_cmd, stream_output=True)


@cli.command()
def stop_server():
    """
    Stop a running gunicorn server.

    When gunicorn is started, a pid file is written to the content/ folder with
    the process ID. We read this file and send a TERM signal to kill the process.
    """
    import signal

    file = Path(current_config.GUNICORN_PID_FILE)
    if file.is_file():
        with open(file) as f:
            pid = int(f.readline().rstrip())
        os.kill(pid, signal.SIGTERM)


@cli.command()
def start_celery():
    """Start the celery worker"""
    cmd = ["celery", "-A", "tasks.celery", "worker", "--beat", "--loglevel=info"]
    exec_cmd(cmd, stream_output=True)


@cli.command()
def clear_logs():
    """Clear all `.log` files in the logs directory"""
    files = current_config.LOGS_DIR.glob("*.log")
    for f in files:
        f.unlink()


@cli.command()
def start_supervisor():
    """Start the supervisor process"""
    cmd = "supervisord -n -c ./supervisord.conf".split()
    exec_cmd(cmd, stream_output=True)


@cli.command()
def stop_supervisor():
    """
    Stop a running supervisor process.

    When supervisor is started, a pid file is written to the logs/ folder with
    the process ID. We read this file and send a TERM signal to kill the process.
    """
    import signal

    file = Path(current_config.SUPERVISOR_PID_FILE)
    pid = get_pid_from_file(file)
    if pid is not None:
        os.kill(pid, signal.SIGTERM)


@cli.command()
def create_db():
    from web import create_app

    app = create_app()
    app.db.create_tables()


@cli.command()
def destroy_db():
    from web import create_app

    app = create_app()
    app.db.destroy_db()


if __name__ == "__main__":
    cli()