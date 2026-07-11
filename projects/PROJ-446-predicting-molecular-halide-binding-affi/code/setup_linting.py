"""
Linting and Formatting Setup Script.

This module provides utilities to configure and run ruff (linting) and black (formatting)
on the project codebase. It ensures necessary configuration files exist and executes
the tools.
"""
import os
import subprocess
import sys
from pathlib import Path

# Define configuration content
RUFF_CONFIG = """[tool.ruff]
line-length = 88
target-version = "py311"
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
]
ignore = [
    "E501",  # line too long (black handles this)
    "B008",  # do not perform function calls in argument defaults
    "C901",  # too complex
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]

[tool.ruff.isort]
known-first-party = ["code"]
"""

BLACK_CONFIG = """[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
    \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''
"""

PYPROJECT_HEADER = """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

"""


def ensure_config_files():
    """
    Create or update pyproject.toml with ruff and black configurations.
    """
    project_root = Path(__file__).resolve().parent.parent
    pyproject_path = project_root / "pyproject.toml"

    # Read existing content if it exists
    existing_content = ""
    if pyproject_path.exists():
        existing_content = pyproject_path.read_text()

    # Check if [tool.ruff] or [tool.black] sections already exist to avoid duplication
    if "[tool.ruff]" in existing_content and "[tool.black]" in existing_content:
        print("Configuration files for ruff and black already exist.")
        return True

    # Prepare new content
    new_content = PYPROJECT_HEADER
    if "[tool.ruff]" not in existing_content:
        new_content += RUFF_CONFIG + "\n"
    if "[tool.black]" not in existing_content:
        new_content += BLACK_CONFIG + "\n"

    # Append any existing content that isn't our tools (simple merge strategy)
    # If the file was empty or just had build-system, we are good.
    # If it had other tools, we append ours.
    if existing_content:
        # Basic check to avoid overwriting unrelated sections if we didn't find ours
        # For safety in this specific task, we assume we are adding to a mostly empty or build-system only file
        # or we append at the end.
        pass 
    
    # Write the combined content. 
    # Strategy: If file exists, we try to preserve it but ensure our sections are there.
    # Since simple string manipulation is risky, we will write the standard config
    # assuming the file is either new or we are appending.
    # A safer approach for a single task: Write the full expected content if it's a new project setup.
    # Given T005 created requirements, pyproject.toml might be empty or non-existent.
    
    if not pyproject_path.exists() or pyproject_path.read_text().strip() == "":
         pyproject_path.write_text(new_content)
    else:
         # Append if not present
         current_text = pyproject_path.read_text()
         if "[tool.ruff]" not in current_text:
             current_text += "\n" + RUFF_CONFIG
         if "[tool.black]" not in current_text:
             current_text += "\n" + BLACK_CONFIG
         pyproject_path.write_text(current_text)

    print(f"Configuration written to {pyproject_path}")
    return True


def run_lint():
    """
    Run ruff on the code directory.
    """
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    
    print("Running ruff linting...")
    try:
        result = subprocess.run(
            ["ruff", "check", str(code_dir)],
            check=False,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("No linting errors found.")
        else:
            print("Linting errors found:")
            print(result.stdout)
            print(result.stderr)
        return result.returncode == 0
    except FileNotFoundError:
        print("Error: ruff not found. Please install it via 'pip install ruff'.")
        return False


def run_format():
    """
    Run black on the code directory.
    """
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    
    print("Running black formatting...")
    try:
        result = subprocess.run(
            ["black", str(code_dir)],
            check=False,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("Formatting complete.")
        else:
            print("Formatting encountered issues:")
            print(result.stdout)
            print(result.stderr)
        return result.returncode == 0
    except FileNotFoundError:
        print("Error: black not found. Please install it via 'pip install black'.")
        return False


def main():
    """
    Main entry point to configure and optionally run lint/format.
    """
    print("Setting up linting and formatting tools...")
    
    # 1. Ensure config files exist
    ensure_config_files()
    
    # 2. Check if dependencies are installed
    try:
        import ruff
        import black
    except ImportError:
        print("Dependencies 'ruff' and 'black' are not installed.")
        print("Please run: pip install ruff black")
        return 1

    # 3. Run lint and format (optional, but good for verification)
    # We run them to ensure the configuration is valid, but we don't fail the task if they find issues.
    # The task is to CONFIGURE them.
    run_lint()
    run_format()
    
    print("Linting and formatting setup complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())