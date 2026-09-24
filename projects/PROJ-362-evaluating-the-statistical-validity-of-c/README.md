# PROJ-362: Evaluating the Statistical Validity of Common Ranking Metrics

## Setup

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Install pre-commit hooks (optional but recommended):
 ```bash
 make install-hooks
 ```

## Usage

### Linting and Formatting

This project uses **ruff** for linting and **black** for formatting. Configuration is in `pyproject.toml`.

- **Check linting (no changes):**
 ```bash
 make lint
 ```

- **Fix linting issues automatically:**
 ```bash
 make lint-fix
 ```

- **Check formatting (no changes):**
 ```bash
 make format-check
 ```

- **Apply formatting:**
 ```bash
 make format
 ```

- **Run all checks:**
 ```bash
 make check
 ```

- **Run all fixes:**
 ```bash
 make fix
 ```

### Pre-commit Hooks

If you installed the pre-commit hooks, they will automatically run `ruff` and `black` on every commit:
```bash
git commit -m "Your message"
```

To run hooks manually on all files:
```bash
make run-hooks
```

### Testing

Run the test suite:
```bash
make test
```

### Cleaning

Clean up cache files and temporary artifacts:
```bash
make clean
```

## Configuration

- **Ruff**: Configured in `pyproject.toml` under `[tool.ruff]`.
- **Black**: Configured in `pyproject.toml` under `[tool.black]`.
- **Pre-commit**: Configured in `.pre-commit-config.yaml`.
- **Make**: Build targets in `Makefile`.

## Development Workflow

1. Create a new branch for your feature or fix.
2. Make your changes.
3. Run `make check` to ensure code style compliance.
4. Run `make test` to ensure tests pass.
5. Commit your changes (pre-commit hooks will run automatically).
6. Push to the remote repository.