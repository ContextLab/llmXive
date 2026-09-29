"""
Configuration for linting and formatting tools used in the llmXive pipeline.

This module provides centralized configuration references for:
- Ruff (linting)
- Black (code formatting)

These settings are primarily intended to be used via command-line arguments
or py.toml/py.cfg files, but are provided here for reference and programmatic access.
"""

# Ruff configuration settings
RUFF_CONFIG = {
    "select": ["E", "F", "W", "I", "N", "UP", "B", "A", "C4", "T20", "PT"],
    "ignore": [
        "E501",  # Line too long (handled by Black)
        "W503",  # Line break before binary operator (handled by Black)
        "W504",  # Line break after binary operator (handled by Black)
    ],
    "max-line-length": 88,  # Matches Black's default
    "target-version": "py311",
    "exclude": [
        "__pycache__",
        ".git",
        ".venv",
        "venv",
        "build",
        "dist",
        "*.egg-info",
    ],
    "per-file-ignores": {
        "tests/*": ["S101"],  # Allow assertions in tests
        "code/*": ["D100"],    # Allow missing docstrings in internal modules
    },
}

# Black configuration settings
BLACK_CONFIG = {
    "line-length": 88,
    "target-version": ["py311"],
    "exclude": r"(\.eggs|\.git|\.hg|\.mypy_cache|\.nox|\.tox|\.venv|venv|_build|buck-build|build|dist|\.egg-info)",
    "include": r"\.pyi?$",
    "skip-string-normalization": False,
    "skip-magic-trailing-comma": False,
}

# Command-line strings for easy invocation
RUFF_CMD = "ruff check ."
RUFF_FIX_CMD = "ruff check --fix ."
RUFF_FORMAT_CMD = "ruff format ."

BLACK_CMD = "black code/ tests/"
BLACK_CHECK_CMD = "black --check code/ tests/"

# Combined linting and formatting command
FULL_LINT_CMD = "ruff check . && black --check code/ tests/"
FULL_FORMAT_CMD = "ruff format . && black code/ tests/"

# CI/CD recommended commands
CI_LINT_CMD = "ruff check . && black --check code/ tests/ && ruff format --check ."
CI_FIX_CMD = "ruff check --fix . && black code/ tests/ && ruff format ."
