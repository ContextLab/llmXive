"""
Configuration and command generation for linting and formatting tools.
Provides standardized commands for Ruff and Black to ensure consistent
code quality and style across the project.
"""
from pathlib import Path


def get_ruff_command() -> str:
    """
    Generate the command to run Ruff linter.
    Returns:
        str: The ruff check command.
    """
    return "ruff check ."


def get_black_command() -> str:
    """
    Generate the command to run Black formatter.
    Returns:
        str: The black formatting command.
    """
    return "black ."


def get_format_check_command() -> str:
    """
    Generate the command to check formatting without modifying files.
    Returns:
        str: The black check command.
    """
    return "black --check ."


def get_lint_check_command() -> str:
    """
    Generate the command to check linting without fixing issues.
    Returns:
        str: The ruff check command (default behavior is check-only unless --fix is added).
    """
    return "ruff check ."
