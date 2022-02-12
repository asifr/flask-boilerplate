.PHONY: docs test

help:
	@echo "  env         create a development environment using virtualenv"
	@echo "  deps        install dependencies using pip"
	@echo "  clean       remove unwanted files like .pyc, .db, .log, cache"
	@echo "  test        run all your tests using py.test"

env:
	python -m venv env

deps:
	. env/bin/activate && \
	pip install -r requirements.txt

clean:
	find . | grep -E "(__pycache__|pytest_cache|\.log|\.pyc|\.DS_Store|\.db|\.pyo$\)" | xargs rm -rf

test:
	. env/bin/activate && \
	pytest

redis:
	redis-server

server:
	python ./manage.py start-server
