# Linting and Formatting Configuration

## Python
This project uses `ruff` for linting and formatting (replacing flake8, isort, and black).

### Setup
```bash
pip install ruff
```

### Usage
- **Check only** (no changes): `ruff check code/`
- **Fix automatically**: `ruff check --fix code/`
- **Format code**: `ruff format code/`
- **Format check**: `ruff format --check code/`

Configuration is in `code/.ruff.toml`.

## R
This project uses `lintr` for static code analysis.

### Setup
```r
install.packages("lintr")
```

### Usage
- **Check file**: `lintr::lint("script.R")`
- **Check directory**: `lintr::lint_dir("R/")`
- **Check package**: `lintr::lint_package()`

Configuration is in `code/R/.lintr`.

### CI Integration
Add `lintr` to your CI pipeline to enforce style on pull requests.