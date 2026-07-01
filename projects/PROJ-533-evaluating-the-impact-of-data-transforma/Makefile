.PHONY: lint format check format-check

lint:
	flake8 code/ tests/

format:
	black code/ tests/

format-check:
	black --check code/ tests/

check: lint format-check