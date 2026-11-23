"""
Linting and Formatting Configuration Generator for llmXive Project.

This module generates configuration files for Ruff (replacing flake8/pylint)
and Black/isort to ensure consistent code style across the project.
"""
import os
import tomlkit
import tomli_w
import json
from pathlib import Path

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent

def get_ruff_config():
    """
    Returns a dictionary representing the Ruff configuration.
    Replaces flake8 and pylint with a modern, fast linter.
    """
    return {
        "target-version": "py39",
        "line-length": 88,
        "select": [
            "E",   # pycodestyle errors
            "W",   # pycodestyle warnings
            "F",   # Pyflakes
            "I",   # isort (sorting)
            "C",   # flake8-comprehensions
            "B",   # flake8-bugbear
            "UP",  # pyupgrade
            "N",   # pep8-naming
            "ANN", # flake8-annotations (optional strictness)
            "S",   # flake8-bandit (security)
            "A",   # flake8-builtins
            "COM", # flake8-commas
            "C4",  # flake8-comprehensions
            "DTZ", # flake8-datetimez
            "T10", # flake8-debugger
            "EXE", # flake8-executable
            "ISC", # flake8-implicit-str-concat
            "ICN", # flake8-import-conventions
            "PIE", # flake8-pie
            "PT",  # flake8-pytest-style
            "Q",   # flake8-quotes
            "RSE", # flake8-raise
            "RET", # flake8-return
            "SIM", # flake8-simplify
            "TCH", # flake8-type-checking
            "ARG", # flake8-unused-arguments
            "PTH", # flake8-use-pathlib
            "ERA", # eradicate
            "PL",  # Pylint
            "TRY", # tryceratops
            "FLY", # flynt
            "NPY", # NumPy-specific rules
            "PERF",# Perflint
            "RUF"  # Ruff-specific rules
        ],
        "ignore": [
            "ANN101", # Missing type annotation for self
            "ANN102", # Missing type annotation for cls
            "ANN204", # Missing return type annotation for special method __init__
            "S101",   # Use of assert detected (common in tests)
            "S105",   # Possible hardcoded password
            "S106",   # Possible hardcoded password
            "S107",   # Possible hardcoded password
            "E501",   # Line too long (handled by Black)
            "COM812", # Trailing comma missing (conflict with Black)
            "ISC001", # Implicit string concatenation (conflict with Black)
            "PLR0913",# Too many arguments in function definition
            "PLR2004",# Magic value used in comparison
            "B905",   # zip() without an explicit strict= parameter (Python 3.10+)
        ],
        "exclude": [
            ".git",
            "__pycache__",
            "build",
            "dist",
            "*.egg-info",
            "venv",
            ".venv",
            "data",
            "docs",
            "migrations"
        ],
        "per-file-ignores": {
            "tests/*": [
                "S101", # Assert allowed in tests
                "ANN",  # Annotations less critical in tests
                "D103"  # Missing docstring in public function
            ],
            "code/utils/errors.py": [
                "D105"  # Missing docstring in magic method
            ]
        },
        "isort": {
            "known-first-party": ["config", "data", "models", "utils", "ingest", "quant", "dge_analysis", "viz", "enrichment"],
            "force-sort-within-sections": true,
            "lines-after-imports": 2
        },
        "pydocstyle": {
            "convention": "numpy"
        },
        "mccabe": {
            "max-complexity": 12
        }
    }

def get_black_config():
    """
    Returns a dictionary representing the Black configuration.
    """
    return {
        "line-length": 88,
        "target-version": ["py39", "py310", "py311"],
        "include": "\\.pyi?$",
        "exclude": """
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
              | data
            )/
        """,
        "skip-string-normalization": false,
        "preview": true
    }

def generate_ruff_toml():
    """
    Generates the ruff.toml configuration file.
    """
    config = get_ruff_config()
    # Convert to TOML format manually or via tomlkit
    # Using tomlkit for better formatting control
    doc = tomlkit.document()
    
    # Add target-version as an array
    if "target-version" in config:
        doc["target-version"] = config.pop("target-version")
    
    # Add simple values
    for key, value in config.items():
        if key == "exclude":
            doc[key] = value
        elif key == "select" or key == "ignore":
            doc[key] = value
        elif key == "per-file-ignores":
            doc[key] = value
        elif key == "isort":
            doc["isort"] = value
        elif key == "pydocstyle":
            doc["pydocstyle"] = value
        elif key == "mccabe":
            doc["mccabe"] = value
    
    # Specific handling for ruff.toml structure
    # Ruff prefers specific sections
    output = tomlkit.document()
    output["target-version"] = config.get("target-version", "py39")
    output["line-length"] = config.get("line-length", 88)
    output["select"] = config.get("select", [])
    output["ignore"] = config.get("ignore", [])
    output["exclude"] = config.get("exclude", [])
    
    if "per-file-ignores" in config:
        output["per-file-ignores"] = config["per-file-ignores"]
    
    if "isort" in config:
        output["isort"] = config["isort"]
    
    if "pydocstyle" in config:
        output["pydocstyle"] = config["pydocstyle"]
    
    if "mccabe" in config:
        output["mccabe"] = config["mccabe"]

    path = PROJECT_ROOT / "ruff.toml"
    with open(path, "w") as f:
        f.write(tomlkit.dumps(output))
    
    return path

def generate_pyproject_toml():
    """
    Generates or updates pyproject.toml with Black and isort settings.
    """
    path = PROJECT_ROOT / "pyproject.toml"
    
    if path.exists():
        with open(path, "rb") as f:
            try:
                import tomli
                doc = tomli.load(f)
            except ImportError:
                # Fallback if tomli not installed, assume simple structure
                doc = {}
    else:
        doc = {}
    
    # Ensure tool sections exist
    if "tool" not in doc:
        doc["tool"] = {}
    
    # Add Black config
    black_config = get_black_config()
    doc["tool"]["black"] = {
        "line-length": black_config["line-length"],
        "target-version": black_config["target-version"],
        "include": black_config["include"],
        "exclude": black_config["exclude"].strip(),
        "skip-string-normalization": black_config["skip-string-normalization"]
    }
    
    # Add isort config
    ruff_config = get_ruff_config()
    if "isort" in ruff_config:
        doc["tool"]["isort"] = ruff_config["isort"]
    
    # Write back
    with open(path, "w") as f:
        import tomli_w
        f.write(tomli_w.dumps(doc))
    
    return path

def main():
    """
    Main entry point to generate all linting and formatting configuration files.
    """
    print("Generating Ruff configuration...")
    ruff_path = generate_ruff_toml()
    print(f"  Created: {ruff_path}")
    
    print("Generating/Updating pyproject.toml (Black & isort)...")
    pyproject_path = generate_pyproject_toml()
    print(f"  Updated: {pyproject_path}")
    
    print("\nConfiguration complete.")
    print("To run linter:   ruff check .")
    print("To format code:  black .")
    print("To sort imports: ruff check --select I .")

if __name__ == "__main__":
    main()
