.PHONY: install test lint format clean build run

install:
	pip install -e .[dev]

test:
	pytest -v --cov=src --cov-report=html

test-watch:
	pytest-watch

lint:
	flake8 src tests
	mypy src

format:
	black src tests

format-check:
	black --check src tests

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build:
	python -m build

run:
	python main.py

dev-setup:
	pip install -e .[dev]

install-deps:
	pip install -r requirements.txt
