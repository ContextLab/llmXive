.PHONY: lint format check

lint:
	ruff check code/

format:
	black code/

check:
	ruff check code/
	black --check code/

fix:
	ruff check --fix code/
	black code/
