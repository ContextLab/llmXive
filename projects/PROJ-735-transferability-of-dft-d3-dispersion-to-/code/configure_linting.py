"""
Configuration script for linting and formatting tools.
This script ensures that .flake8 and pyproject.toml (for black/isort)
are correctly set up in the project root.
"""
import os
from pathlib import Path

def ensure_config_files():
    """Create or update linting configuration files if missing."""
    project_root = Path(__file__).resolve().parent.parent

    # 1. Ensure .flake8 exists
    flake8_path = project_root / ".flake8"
    if not flake8_path.exists():
        content = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    .eggs,
    build,
    dist,
    *.egg-info
per-file-ignores =
    code/__init__.py:F401
    tests/__init__.py:F401
"""
        flake8_path.write_text(content)
        print(f"Created {flake8_path}")
    else:
        print(f"Found existing {flake8_path}")

    # 2. Ensure pyproject.toml exists with [tool.black] and [tool.isort]
    pyproject_path = project_root / "pyproject.toml"
    black_config = """[tool.black]
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
  | \\.egg
)/
'''

[tool.isort]
profile = "black"
line_length = 88
known_first_party = ["generate_synthetic_data", "setup_directories"]
skip = [".git", ".venv", "build", "dist"]
"""

    if pyproject_path.exists():
        current_content = pyproject_path.read_text()
        if "[tool.black]" not in current_content:
            # Append black config
            with open(pyproject_path, "a") as f:
                f.write("\n" + black_config)
            print(f"Appended [tool.black] and [tool.isort] to {pyproject_path}")
        else:
            print(f"Found existing [tool.black] in {pyproject_path}")
    else:
        pyproject_path.write_text(black_config)
        print(f"Created {pyproject_path} with linting config")

def main():
    """Entry point for the configuration script."""
    print("Configuring linting (flake8) and formatting (black/isort) tools...")
    ensure_config_files()
    print("Configuration complete.")
    print("\nYou can now run:")
    print("  flake8 code/ tests/")
    print("  black --check code/ tests/")
    print("  isort --check-only code/ tests/")

if __name__ == "__main__":
    main()