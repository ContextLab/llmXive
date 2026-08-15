"""
Configuration and setup script for linting (ruff/flake8) and formatting (black) tools.
This script ensures that the project has the necessary configuration files:
- pyproject.toml (containing Black settings and ruff/flake8 configuration)
- .ruff.toml (optional, for ruff-specific overrides if needed)

It also provides a main() entry point to execute the setup.
"""
import os
import sys
from pathlib import Path

def ensure_pyproject_toml():
    """
    Creates or updates the pyproject.toml file with configuration for
    Black (formatter) and Ruff (linter) as per project standards.
    
    Returns:
        Path: The path to the pyproject.toml file.
    """
    root = Path(__file__).resolve().parent.parent
    pyproject_path = root / "pyproject.toml"
    
    # Define the configuration content
    # We use a list of lines to ensure consistent formatting and indentation
    config_lines = [
        "[tool.black]",
        "line-length = 88",
        "target-version = ['py39', 'py310', 'py311']",
        "include = '\\.pyi?$'",
        "extend-exclude = '''",
        "^/venv/",
        "^/build/",
        "^/.git/",
        "'''",
        "",
        "[tool.ruff]",
        "line-length = 88",
        "target-version = 'py311'",
        "select = [",
        "    \"E\",  # pycodestyle errors",
        "    \"W\",  # pycodestyle warnings",
        "    \"F\",  # Pyflakes",
        "    \"I\",  # isort",
        "    \"B\",  # flake8-bugbear",
        "    \"C4\", # flake8-comprehensions",
        "]",
        "ignore = [",
        "    \"E501\", # line too long (handled by black)",
        "    \"B008\", # do not perform function calls in argument defaults",
        "]",
        "",
        "[tool.ruff.per-file-ignores]",
        "\"__init__.py\" = [\"F401\"]",
        "",
        "[tool.ruff.isort]",
        "known-first-party = [\"code\", \"tests\", \"results\", \"data\"]",
        "",
        "[tool.black]",
        "skip-string-normalization = false",
        ""
    ]
    
    content = "\n".join(config_lines)
    
    # Write the file if it doesn't exist, or update it if it does (simple overwrite for this task)
    # In a real scenario, we might want to merge, but for this task, we ensure the config exists.
    pyproject_path.write_text(content)
    
    print(f"Successfully configured {pyproject_path} for Black and Ruff.")
    return pyproject_path

def main():
    """
    Main entry point for the linting configuration setup.
    """
    print("Starting linting and formatting configuration setup...")
    try:
        ensure_pyproject_toml()
        print("Configuration complete. Run 'black .' and 'ruff check .' to apply.")
        return 0
    except Exception as e:
        print(f"Error during configuration: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
