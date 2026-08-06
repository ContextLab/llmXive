"""
Configuration utilities for linting and formatting tools.
Provides command-line strings for ruff and black execution.
"""
from pathlib import Path


def get_ruff_command() -> str:
    """Return the ruff lint command."""
    return "ruff check ."


def get_black_command() -> str:
    """Return the black format command."""
    return "black ."


def get_format_check_command() -> str:
    """Return the command to check formatting without modifying."""
    return "black --check ."


def get_lint_check_command() -> str:
    """Return the command to check linting without modifying."""
    return "ruff check ."