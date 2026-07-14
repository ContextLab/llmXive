import json
import os
import sys
from pathlib import Path

def create_ruff_config():
    """
    Creates a .ruff.toml configuration file for linting.
    """
    project_root = Path.cwd()
    config_file = project_root / ".ruff.toml"
    
    config_content = """[lint]
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
]

[lint.isort]
known-first-party = ["code"]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    
    if not config_file.exists():
        config_file.write_text(config_content, encoding="utf-8")
        print(f"Created .ruff.toml: {config_file}")
    else:
        print(f".ruff.toml already exists: {config_file}")
    
    return config_file

def create_black_config():
    """
    Creates a pyproject.toml section for Black formatting configuration.
    """
    project_root = Path.cwd()
    pyproject_file = project_root / "pyproject.toml"
    
    black_section = """[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \.git
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

[tool.ruff]
# If ruff is used for linting, we can reference the .ruff.toml here or inline config
"""
    
    if pyproject_file.exists():
        existing = pyproject_file.read_text(encoding="utf-8")
        if "[tool.black]" not in existing:
            with open(pyproject_file, "a", encoding="utf-8") as f:
                f.write("\n" + black_section)
            print(f"Updated pyproject.toml with Black config: {pyproject_file}")
        else:
            print(f"pyproject.toml already contains Black config: {pyproject_file}")
    else:
        pyproject_file.write_text(black_section, encoding="utf-8")
        print(f"Created pyproject.toml with Black config: {pyproject_file}")
    
    return pyproject_file

def main():
    """
    Main entry point to setup linting and formatting tools.
    """
    try:
        create_ruff_config()
        create_black_config()
        print("Linting and formatting tools configured successfully.")
        return 0
    except Exception as e:
        print(f"Error configuring linting/formatting: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())