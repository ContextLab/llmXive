import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str]) -> None:
    """Execute a command and raise an error if it fails."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed with code {result.returncode}")

def main() -> None:
    """Configure linting and formatting tools for the project."""
    root = Path(__file__).parent.parent
    pyproject = root / "pyproject.toml"
    requirements = root / "requirements.txt"

    # 1. Install dependencies
    run_command([sys.executable, "-m", "pip", "install", "-r", str(requirements)])

    # 2. Create pyproject.toml configuration for ruff and black if it doesn't exist
    if not pyproject.exists():
        config_content = """[tool.black]
line-length = 88
target-version = ['py310']

[tool.ruff]
line-length = 88
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"] # Allow unused imports in __init__.py

[tool.ruff.isort]
known-first-party = ["code", "utils"]
"""
        pyproject.write_text(config_content)
        print(f"Created {pyproject}")
    else:
        print(f"{pyproject} already exists. Skipping creation.")

    # 3. Format code with black
    run_command([sys.executable, "-m", "black", "code/", "tests/"])

    # 4. Lint code with ruff
    run_command([sys.executable, "-m", "ruff", "check", "code/", "tests/"])

    print("Linting and formatting configuration complete.")

if __name__ == "__main__":
    main()