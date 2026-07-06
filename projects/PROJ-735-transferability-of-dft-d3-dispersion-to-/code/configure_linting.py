"""
Linting and formatting configuration for the llmXive project.

This module ensures that configuration files for flake8 and black are present
in the project root. It also provides a main entry point to run these tools.
"""
import os
from pathlib import Path
import subprocess
import sys

def ensure_config_files():
    """Create .flake8 and pyproject.toml configuration files if they don't exist."""
    root = Path(__file__).parent.parent

    # flake8 configuration
    flake8_config = root / ".flake8"
    if not flake8_config.exists():
        content = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    build,
    dist,
    .eggs,
    *.egg-info
per-file-ignores =
    # Allow unused imports in __init__.py
    */__init__.py:F401
"""
        flake8_config.write_text(content)
        print(f"Created {flake8_config}")

    # Black configuration (in pyproject.toml)
    pyproject = root / "pyproject.toml"
    black_section = """[tool.black]
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
  | \\.egg-info
)/
'''
"""

    if pyproject.exists():
        existing = pyproject.read_text()
        if "[tool.black]" not in existing:
            pyproject.write_text(existing + "\n" + black_section)
            print(f"Added Black configuration to {pyproject}")
        else:
            print(f"Black configuration already present in {pyproject}")
    else:
        pyproject.write_text(black_section)
        print(f"Created {pyproject} with Black configuration")

    # isort configuration (in pyproject.toml)
    isort_section = """[tool.isort]
profile = "black"
line_length = 88
skip = [".git", "__pycache__", "build", "dist", ".eggs", "*.egg-info"]
known_first_party = ["code", "tests"]
"""

    if pyproject.exists():
        existing = pyproject.read_text()
        if "[tool.isort]" not in existing:
            pyproject.write_text(existing + "\n" + isort_section)
            print(f"Added isort configuration to {pyproject}")
        else:
            print(f"isort configuration already present in {pyproject}")
    else:
        # Should not happen as we create it above, but just in case
        pyproject.write_text(isort_section)
        print(f"Created {pyproject} with isort configuration")

def run_flake8():
    """Run flake8 on the code and tests directories."""
    root = Path(__file__).parent.parent
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", "code", "tests"],
            cwd=root,
            capture_output=False,
            check=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        return False

def run_black(check_only=True):
    """Run black on the code and tests directories."""
    root = Path(__file__).parent.parent
    args = [sys.executable, "-m", "black", "--check"] if check_only else [sys.executable, "-m", "black"]
    args.extend(["code", "tests"])
    try:
        result = subprocess.run(
            args,
            cwd=root,
            capture_output=False,
            check=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        return False

def run_isort(check_only=True):
    """Run isort on the code and tests directories."""
    root = Path(__file__).parent.parent
    args = [sys.executable, "-m", "isort", "--check-only"] if check_only else [sys.executable, "-m", "isort"]
    args.extend(["code", "tests"])
    try:
        result = subprocess.run(
            args,
            cwd=root,
            capture_output=False,
            check=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        return False

def main():
    """Main entry point for configuring and running linting/formatting."""
    print("Setting up linting and formatting configuration...")
    ensure_config_files()

    print("\nRunning isort (sorting imports)...")
    if not run_isort(check_only=False):
        print("isort completed with changes or errors.")
    else:
        print("isort passed.")

    print("\nRunning black (formatting)...")
    if not run_black(check_only=False):
        print("black completed with changes or errors.")
    else:
        print("black passed.")

    print("\nRunning flake8 (linting)...")
    if run_flake8():
        print("flake8 passed.")
    else:
        print("flake8 found issues.")

if __name__ == "__main__":
    main()