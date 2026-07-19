"""
Linting configuration constants for the project.

This module centralizes flake8 and black configuration to ensure
consistent code style across the project.
"""

# Black formatting settings
BLACK_LINE_LENGTH = 100
BLACK_SKIP_STRING_NORMALIZATION = False

# Flake8 settings
FLAKE8_MAX_LINE_LENGTH = 100
FLAKE8_IGNORE = [
    "E501",  # Line too long (handled by black)
    "W503",  # Line break before binary operator (black preference)
]
FLAKE8_MAX_COMPLEXITY = 15
FLAKE8_EXCLUDE = [
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    "data",
    "state",
    "docs",
]

def get_black_config():
    """Return a dictionary of black configuration options."""
    return {
        "line_length": BLACK_LINE_LENGTH,
        "skip_string_normalization": BLACK_SKIP_STRING_NORMALIZATION,
    }

def get_flake8_config():
    """Return a dictionary of flake8 configuration options."""
    return {
        "max_line_length": FLAKE8_MAX_LINE_LENGTH,
        "ignore": FLAKE8_IGNORE,
        "max_complexity": FLAKE8_MAX_COMPLEXITY,
        "exclude": FLAKE8_EXCLUDE,
    }
