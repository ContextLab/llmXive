"""
Linting and Formatting Configuration Runner for llmXive Project.

This script installs and configures Ruff (linter) and Black (formatter)
based on the project's requirements. It serves as the entry point for
setting up the code quality infrastructure as per task T003.

Usage:
    python code/tools/lint_format.py
"""

import subprocess
import sys
import os
import tomli_w
import tomllib


def ensure_requirements():
    """Ensure ruff and black are installed."""
    packages = ["ruff", "black"]
    for package in packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✓ {package} is already installed.")
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ {package} installed successfully.")


def create_ruff_config():
    """Create or update pyproject.toml with Ruff configuration."""
    config_path = "pyproject.toml"
    
    # Read existing config if it exists
    existing_config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "rb") as f:
                existing_config = tomllib.load(f)
        except Exception as e:
            print(f"Warning: Could not read existing pyproject.toml: {e}")

    # Define Ruff configuration
    ruff_config = {
        "line-length": 100,
        "target-version": "py310",
        "lint": {
            "select": [
                "E",   # pycodestyle errors
                "W",   # pycodestyle warnings
                "F",   # pyflakes
                "I",   # isort
                "C",   # flake8-comprehensions
                "B",   # flake8-bugbear
                "UP",  # pyupgrade
                "RUF", # ruff specific rules
            ],
            "ignore": [
                "E501", # line too long (handled by black)
                "B008", # do not perform function calls in argument defaults
            ],
            "per-file-ignores": {
                "__init__.py": ["F401"], # allow unused imports in init files
                "tests/*": ["S101"],     # allow assert in tests
            },
        },
    }

    # Ensure tool.ruff section exists
    if "tool" not in existing_config:
        existing_config["tool"] = {}
    if "ruff" not in existing_config["tool"]:
        existing_config["tool"]["ruff"] = ruff_config
    else:
        # Merge configurations
        existing_config["tool"]["ruff"].update(ruff_config)

    # Write updated config
    with open(config_path, "wb") as f:
        tomli_w.dump(existing_config, f)
    
    print(f"✓ Ruff configuration written to {config_path}")


def create_black_config():
    """Ensure Black configuration exists in pyproject.toml."""
    config_path = "pyproject.toml"
    
    # Read existing config
    existing_config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "rb") as f:
                existing_config = tomllib.load(f)
        except Exception:
            pass

    # Define Black configuration
    black_config = {
        "line-length": 100,
        "target-version": ["py310"],
        "exclude": r"""
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
        """,
    }

    # Ensure tool.black section exists
    if "tool" not in existing_config:
        existing_config["tool"] = {}
    if "black" not in existing_config["tool"]:
        existing_config["tool"]["black"] = black_config
    else:
        existing_config["tool"]["black"].update(black_config)

    # Write updated config
    with open(config_path, "wb") as f:
        tomli_w.dump(existing_config, f)
    
    print(f"✓ Black configuration written to {config_path}")


def create_vscode_settings():
    """Create .vscode/settings.json for IDE integration."""
    vscode_dir = ".vscode"
    settings_path = os.path.join(vscode_dir, "settings.json")
    
    os.makedirs(vscode_dir, exist_ok=True)
    
    settings = {
        "editor.defaultFormatter": "ms-python.black-formatter",
        "editor.formatOnSave": True,
        "editor.codeActionsOnSave": {
            "source.organizeImports": "explicit"
        },
        "python.linting.enabled": True,
        "python.linting.ruffEnabled": True,
        "python.formatting.provider": "black",
        "python.formatting.blackPath": "black",
        "[python]": {
            "editor.defaultFormatter": "ms-python.black-formatter"
        }
    }
    
    import json
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=4)
    
    print(f"✓ VS Code settings written to {settings_path}")


def main():
    """Main entry point for linting and formatting setup."""
    print("Setting up linting (Ruff) and formatting (Black) tools...")
    print("-" * 50)
    
    # Step 1: Ensure packages are installed
    ensure_requirements()
    print()
    
    # Step 2: Create configuration files
    create_ruff_config()
    create_black_config()
    create_vscode_settings()
    
    print()
    print("-" * 50)
    print("✓ Linting and formatting setup complete!")
    print()
    print("To format code:   black code/")
    print("To lint code:     ruff check code/")
    print("To fix linting:   ruff check --fix code/")


if __name__ == "__main__":
    main()
