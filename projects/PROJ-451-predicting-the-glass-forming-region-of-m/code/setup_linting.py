"""
Setup script to configure linting (ruff) and formatting (black) tools.
This script creates the necessary configuration files and updates requirements.txt.
"""
import os
import subprocess
import sys
import json
from pathlib import Path


def run_command(command: list) -> bool:
    """Run a shell command and return True if successful."""
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(command)}")
        print(f"Error: {e}")
        return False


def update_requirements() -> None:
    """Add ruff and black to requirements.txt if not already present."""
    requirements_path = Path("requirements.txt")
    if not requirements_path.exists():
        print("requirements.txt not found. Creating a new one.")
        requirements_path.write_text("# Project dependencies\n")

    content = requirements_path.read_text()
    new_deps = ["ruff", "black"]
    updated = False

    for dep in new_deps:
        if dep not in content:
            content += f"{dep}\n"
            updated = True
            print(f"Added {dep} to requirements.txt")

    if updated:
        requirements_path.write_text(content)
    else:
        print("ruff and black are already in requirements.txt")


def create_pyproject_toml() -> None:
    """Create pyproject.toml with ruff and black configurations."""
    config_content = """[tool.black]
line-length = 88
target-version = ['py311']
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
target-version = "py311"
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
    "C901", # too complex
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]

[tool.ruff.isort]
known-first-party = ["code"]
"""
    pyproject_path = Path("pyproject.toml")
    if pyproject_path.exists():
        print("pyproject.toml already exists. Updating configuration...")
        # Simple append strategy for safety; in a real scenario, we'd parse and merge
        existing = pyproject_path.read_text()
        if "[tool.black]" not in existing:
            pyproject_path.write_text(existing + "\n" + config_content)
        else:
            print("Configuration sections already present.")
    else:
        pyproject_path.write_text(config_content)
        print("Created pyproject.toml with ruff and black configurations.")


def main() -> None:
    """Main entry point for the setup script."""
    print("Setting up linting and formatting tools...")

    # Update requirements.txt
    update_requirements()

    # Create pyproject.toml
    create_pyproject_toml()

    # Try to install the tools if pip is available
    print("Attempting to install tools via pip...")
    if run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]):
        print("Successfully installed dependencies.")
    else:
        print("Failed to install dependencies. Please install manually.")

    print("Setup complete. Run 'ruff check .' to lint and 'black .' to format.")


if __name__ == "__main__":
    main()