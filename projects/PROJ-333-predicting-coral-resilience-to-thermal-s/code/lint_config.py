"""
Configuration generators for linting and formatting tools.
Generates ruff.toml and pyproject.toml with Black and isort settings.
"""
import os
import tomlkit
import tomli_w
import json
from pathlib import Path

def get_ruff_config():
    """Return the configuration dictionary for ruff."""
    return {
        "target-version": "py39",
        "line-length": 88,
        "select": [
            "E",   # pycodestyle errors
            "W",   # pycodestyle warnings
            "F",   # Pyflakes
            "I",   # isort
            "C",   # flake8-comprehensions
            "B",   # flake8-bugbear
            "UP",  # pyupgrade
            "N",   # pep8-naming
            "PT",  # pytest
            "RUF"  # ruff-specific rules
        ],
        "ignore": [
            "E501", # Line too long (handled by black)
            "B008", # Do not perform function call in argument defaults (common in dataclasses)
            "C901", # Too complex (temporary relaxation)
            "N803", # Argument name should be lowercase (temporary relaxation)
            "N806", # Variable in function should be lowercase (temporary relaxation)
        ],
        "exclude": [
            ".git",
            "__pycache__",
            ".venv",
            "venv",
            "data",
            "build",
            "dist"
        ],
        "per-file-ignores": {
            "tests/*": ["PT001", "PT004", "PT006"] # Relax pytest rules in tests
        }
    }

def get_black_config():
    """Return the configuration dictionary for black."""
    return {
        "line-length": 88,
        "target-version": ["py39"],
        "exclude": r"/(\.git|__pycache__|\.venv|venv|data|build|dist)/",
        "skip-string-normalization": False,
        "preview": True
    }

def generate_ruff_toml():
    """Generate ruff.toml configuration file."""
    config = get_ruff_config()
    # Convert to TOML format manually or use tomlkit
    # Since tomlkit is available, we use it for proper formatting
    doc = tomlkit.document()
    
    # Add target-version as a list
    doc["target-version"] = config["target-version"]
    doc["line-length"] = config["line-length"]
    
    # Add select list
    doc["select"] = config["select"]
    
    # Add ignore list
    doc["ignore"] = config["ignore"]
    
    # Add exclude list
    doc["exclude"] = config["exclude"]
    
    # Add per-file-ignores
    if "per-file-ignores" in config:
        doc["per-file-ignores"] = config["per-file-ignores"]

    # Write to file
    output_path = Path("ruff.toml")
    with open(output_path, "w") as f:
        f.write(tomlkit.dumps(doc))
    
    print(f"Generated {output_path}")

def generate_pyproject_toml():
    """Generate or update pyproject.toml with Black and isort settings."""
    output_path = Path("pyproject.toml")
    
    # Read existing if present
    if output_path.exists():
        with open(output_path, "rb") as f:
            import tomli
            try:
                existing = tomli.load(f)
            except Exception:
                existing = {}
    else:
        existing = {}

    # Ensure [tool] section exists
    if "tool" not in existing:
        existing["tool"] = {}

    # Configure Black
    black_config = get_black_config()
    existing["tool"]["black"] = black_config

    # Configure isort
    existing["tool"]["isort"] = {
        "profile": "black",
        "line_length": 88,
        "skip_gitignore": True,
        "known_first_party": ["code", "data", "utils", "models"]
    }

    # Write back
    with open(output_path, "wb") as f:
        tomli_w.dump(existing, f)
    
    print(f"Generated {output_path}")

def main():
    """Main entry point for lint_config."""
    print("Generating linting and formatting configuration files...")
    generate_ruff_toml()
    generate_pyproject_toml()
    print("Configuration files generated successfully.")

if __name__ == "__main__":
    main()
