"""
Configuration generation for linting (ruff) and formatting (black) tools.
This module creates the necessary configuration files for the project.
"""
import os
import sys
from pathlib import Path
import toml

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

def write_ruff_config():
    """Create .ruff.toml configuration file."""
    config_content = """[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
]

[lint.per-file-ignores]
"__init__.py" = ["F401"] # Ignore unused imports in __init__.py

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    config_path = PROJECT_ROOT / ".ruff.toml"
    with open(config_path, "w") as f:
        f.write(config_content)
    print(f"Created {config_path}")
    return config_path

def write_black_config():
    """Create pyproject.toml with Black configuration."""
    # Read existing pyproject.toml if it exists
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    existing_config = {}
    
    if pyproject_path.exists():
        try:
            with open(pyproject_path, "r") as f:
                existing_config = toml.load(f)
        except Exception:
            existing_config = {}

    # Ensure [tool.black] section exists
    if "tool" not in existing_config:
        existing_config["tool"] = {}
    existing_config["tool"]["black"] = {
        "line-length": 88,
        "target-version": ["py310"],
        "include": r'\.pyi?$',
        "exclude": r'''
        (
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
        )
        '''
    }

    with open(pyproject_path, "w") as f:
        toml.dump(existing_config, f)
    print(f"Updated {pyproject_path} with Black configuration")
    return pyproject_path

def write_pre_commit_config():
    """Create .pre-commit-config.yaml for pre-commit hooks."""
    config_content = """repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
- id: ruff
  args: [--fix]
- id: ruff-format
  
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
- id: black
  language_version: python3.10
"""
    config_path = PROJECT_ROOT / ".pre-commit-config.yaml"
    with open(config_path, "w") as f:
        f.write(config_content)
    print(f"Created {config_path}")
    return config_path

def update_requirements():
    """Add linting dependencies to requirements.txt if not present."""
    requirements_path = PROJECT_ROOT / "requirements.txt"
    if not requirements_path.exists():
        print(f"Warning: {requirements_path} not found. Creating new file.")
        requirements_path.touch()

    with open(requirements_path, "r") as f:
        lines = f.readlines()

    existing_packages = [line.split("==")[0].strip() for line in lines if "==" in line]
    existing_packages += [line.strip() for line in lines if not line.startswith("#") and "==" not in line]

    new_deps = [
        "ruff>=0.1.6",
        "black>=23.11.0",
        "pre-commit>=3.5.0"
    ]

    updated = False
    for dep in new_deps:
        pkg_name = dep.split(">=")[0]
        if pkg_name not in existing_packages:
            lines.append(f"{dep}\n")
            updated = True
            print(f"Added {dep} to requirements.txt")

    if updated:
        with open(requirements_path, "w") as f:
            f.writelines(lines)
    else:
        print("All linting dependencies already present in requirements.txt")

def main():
    """Generate all linting and formatting configurations."""
    print("Configuring linting and formatting tools...")
    
    try:
        write_ruff_config()
        write_black_config()
        write_pre_commit_config()
        update_requirements()
        
        print("\nConfiguration complete!")
        print("To install pre-commit hooks, run: pre-commit install")
        print("To run linter: ruff check .")
        print("To run formatter: black .")
        print("To run both: pre-commit run --all-files")
        
    except Exception as e:
        print(f"Error during configuration: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()