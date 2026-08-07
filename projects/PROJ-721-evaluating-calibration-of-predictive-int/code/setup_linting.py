from __future__ import annotations

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd: list[str]) -> None:
    """Run a shell command and raise an error if it fails."""
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True, text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Command failed with exit code {e.returncode}: {e.stderr}") from e


def main() -> None:
    """Install and configure linting (ruff) and formatting (black) tools."""
    # Ensure tools are installed
    run_command([sys.executable, "-m", "pip", "install", "ruff", "black", "--quiet"])

    # Create pyproject.toml with configuration if it doesn't exist
    root = Path(__file__).resolve().parent.parent
    pyproject_path = root / "pyproject.toml"

    if pyproject_path.exists():
        content = pyproject_path.read_text()
        if "[tool.black]" in content and "[tool.ruff]" in content:
            print("Configuration already exists in pyproject.toml")
            return
        print("Appending configuration to existing pyproject.toml")
    else:
        content = ""
        print("Creating new pyproject.toml")

    config = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \\.git
  | \\.mypy_cache
  | \\.tox
  | venv
  | build
  | dist
)/
'''

[tool.ruff]
line-length = 88
target-version = "py311"
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"] # Ignore unused imports in __init__.py

[tool.ruff.isort]
known-first-party = ["download", "metrics", "models", "stratify", "setup_linting"]
"""

    with open(pyproject_path, "w") as f:
        f.write(content + config)

    print("Linting and formatting configuration complete.")


if __name__ == "__main__":
    main()