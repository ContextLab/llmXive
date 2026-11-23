.PHONY: lint lint-check format

lint-check:
    @echo "Running flake8..."
    flake8 code/ tests/ --config=.flake8
    @echo "Running black check..."
    black --check code/ tests/ --config=pyproject.toml
    @echo "Lint check passed."

lint:
    @echo "Running flake8..."
    flake8 code/ tests/ --config=.flake8
    @echo "Running black check..."
    black --check code/ tests/ --config=pyproject.toml
    @echo "Lint check passed."

format:
    @echo "Formatting code with black..."
    black code/ tests/ --config=pyproject.toml
    @echo "Formatting complete."
