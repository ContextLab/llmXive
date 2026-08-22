"""
Linting and Formatting Setup Script.

This module provides utilities to configure and run linting (ruff)
and formatting (black) tools for the project.
"""
from __future__ import annotations

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """
    Execute a shell command and report success/failure.

    Args:
        cmd: List of command arguments.
        description: Human-readable description of the action.

    Returns:
        True if the command succeeded (exit code 0), False otherwise.
    """
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {description} failed with exit code {e.returncode}")
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return False

def main() -> int:
    """
    Main entry point to install and configure linting tools.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    # Determine project root (assuming script is in code/)
    project_root = Path(__file__).parent.parent
    config_file = project_root / "pyproject.toml"

    print(f"Project root detected at: {project_root}")

    # 1. Install tools if not present
    tools = [
        ("ruff", ["ruff", "--version"]),
        ("black", ["black", "--version"]),
    ]

    installed = True
    for name, check_cmd in tools:
        if not run_command(check_cmd, f"Check if {name} is installed"):
            print(f"Installing {name}...")
            if not run_command([sys.executable, "-m", "pip", "install", name], f"Install {name}"):
                installed = False
                break

    if not installed:
        print("Failed to install required tools.")
        return 1

    # 2. Generate configuration file (pyproject.toml) if missing
    if not config_file.exists():
        print(f"Creating {config_file} with ruff and black configuration...")
        config_content = """[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311']
include = '\\.pyi?$'
exclude = '''
/(
    \\.git
  | \\.hg
  | \\.mypy_cache
  | \\.tox
  | \\.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''

[tool.ruff]
line-length = 88
target-version = "py39"
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
]
ignore = [
    "E501",  # line too long (handled by black)
    "B008",  # do not perform function calls in argument defaults
    "C901",  # too complex
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]  # Allow unused imports in init files

[tool.ruff.isort]
known-first-party = ["download", "metrics", "models", "recalibration", "stratify"]
"""
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(config_content)
        print(f"Configuration written to {config_file}")
    else:
        print(f"{config_file} already exists. Skipping generation.")

    # 3. Run initial format and lint checks
    print("\n--- Running Black Formatter ---")
    if not run_command(
        ["black", "--check", "--diff", "code/", "tests/"],
        "Check formatting with Black"
    ):
        print("Note: Formatting check failed. Run 'black code/ tests/' to fix.")

    print("\n--- Running Ruff Linter ---")
    if not run_command(
        ["ruff", "check", "code/", "tests/"],
        "Check linting with Ruff"
    ):
        print("Note: Linting check failed. Run 'ruff check code/ tests/ --fix' to fix.")

    print("\nLinting and formatting setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())