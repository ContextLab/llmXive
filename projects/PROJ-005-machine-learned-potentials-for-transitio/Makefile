.PHONY: lint format install-dev

install-dev:
	pip install -r requirements-dev.txt
	pip install -e .

format:
	black code/ tests/
	isort code/ tests/

lint:
	flake8 code/ tests/
	isort --check-only code/ tests/
	black --check code/ tests/

pre-commit:
	pre-commit run --all-files