"""
Linting and formatting configuration for the project.
This module provides constants and helper functions for running ruff and black.
"""

# Ruff configuration
RUFF_COMMAND = [
    "ruff", "check",
    "--select", "E,W,F,I,N,B,C4,T20",
    "--ignore", "E501",  # Line too long (handled by black)
    "--show-source",
    "--statistics",
]

# Black configuration
BLACK_COMMAND = [
    "black",
    "--line-length", "88",
    "--target-version", "py311",
    "--exclude", r"(\.git|\.mypy_cache|__pycache__|\.venv|venv|build|dist)",
]

def get_ruff_command():
    """Returns the list of arguments for running ruff."""
    return RUFF_COMMAND.copy()

def get_black_command():
    """Returns the list of arguments for running black."""
    return BLACK_COMMAND.copy()
