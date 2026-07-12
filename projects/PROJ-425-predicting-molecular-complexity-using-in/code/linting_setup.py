import os
import subprocess
import sys
from pathlib import Path

def install_dependencies():
    """
    Installs ruff and black using pip.
    These are the tools required for linting and formatting.
    """
    print("Installing linting and formatting tools...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ruff", "black"])
        print("Successfully installed ruff and black.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)

def create_config_files():
    """
    Creates configuration files for ruff and black.
    - pyproject.toml (for black and ruff settings)
    """
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"

    if pyproject_path.exists():
        print("pyproject.toml already exists. Skipping creation.")
        # We could update it, but for this task we assume creation is sufficient
        # or that the user will merge. To be safe, we create a backup or skip.
        # Given the task is "Configure", creating the file if missing is the primary goal.
        return

    config_content = """[tool.black]
line-length = 88
target-version = ['py311']
include = 'code/'
extend-exclude = '''
# A regex to exclude files
(
    __pycache__
    | .git
)
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
    "E501", # Line too long (black handles this)
    "B008", # Do not perform function call in argument defaults (common in ML)
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]
"""
    try:
        pyproject_path.write_text(config_content)
        print(f"Created configuration at {pyproject_path}")
    except IOError as e:
        print(f"Error writing configuration file: {e}")
        sys.exit(1)

def main():
    """
    Main entry point to configure linting and formatting tools.
    """
    print("Starting linting and formatting configuration...")
    install_dependencies()
    create_config_files()
    print("Configuration complete. You can now run 'ruff check .' and 'black .' to lint and format.")

if __name__ == "__main__":
    main()