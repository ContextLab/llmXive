.PHONY: lint format check

lint:
	ruff check code/ src/ tests/

format:
	black code/ src/ tests/
	ruff check --fix code/ src/ tests/

check:
	black --check code/ src/ tests/
	ruff check code/ src/ tests/
