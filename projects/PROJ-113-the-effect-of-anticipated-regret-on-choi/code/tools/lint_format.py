"""
Linting and formatting configuration tool for the project.
Creates configuration files for Ruff and Black.
"""
import subprocess
import sys
import os
import tomli_w
import tomllib
from pathlib import Path

def ensure_requirements():
    """Ensure required packages are installed."""
    required = ["ruff", "black", "tomli", "tomli_w"]
    missing = []
    for pkg in required:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"Installing missing packages: {missing}")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
        print("Packages installed successfully.")
    else:
        print("All required packages are already installed.")

def create_ruff_config():
    """Create a ruff.toml configuration file."""
    config_path = Path("ruff.toml")
    if config_path.exists():
        print(f"ruff.toml already exists at {config_path}")
        return

    ruff_config = {
        "target-version": "py310",
        "line-length": 88,
        "select": [
            "E",  # pycodestyle errors
            "W",  # pycodestyle warnings
            "F",  # Pyflakes
            "I",  # isort
            "B",  # flake8-bugbear
            "C4", # flake8-comprehensions
            "UP", # pyupgrade
        ],
        "ignore": [
            "E501", # line too long (handled by black)
            "B008", # do not perform function calls in argument defaults
        ],
        "exclude": [
            ".git",
            "__pycache__",
            ".eggs",
            "*.egg-info",
            "venv",
            ".venv",
            "build",
            "dist",
        ],
        "per-file-ignores": {
            "__init__.py": ["F401"], # Ignore unused imports in __init__.py
        },
    }

    with open(config_path, "wb") as f:
        tomli_w.dump(ruff_config, f)

    print(f"Created ruff configuration at {config_path}")

def create_black_config():
    """Create a pyproject.toml section for Black configuration."""
    config_path = Path("pyproject.toml")
    
    # Check if pyproject.toml exists and has [tool.black]
    if config_path.exists():
        with open(config_path, "rb") as f:
            try:
                config = tomllib.load(f)
                if "tool" in config and "black" in config["tool"]:
                    print(f"[tool.black] already exists in {config_path}")
                    return
            except tomllib.TOMLDecodeError:
                print(f"Warning: {config_path} is not valid TOML, appending new section")

    # Append Black configuration
    black_section = """
[tool.black]
line-length = 88
target-version = ['py310']
include = '\\.pyi?$'
exclude = '''
/(
    \\.git
  | \\.eggs
  | venv
  | \\.venv
  | build
  | dist
  | \\.mypy_cache
)/
'''
"""
    with open(config_path, "a") as f:
        f.write(black_section)
    
    print(f"Added [tool.black] configuration to {config_path}")

def create_vscode_settings():
    """Create .vscode/settings.json for VS Code integration."""
    vscode_dir = Path(".vscode")
    vscode_dir.mkdir(exist_ok=True)
    
    settings_path = vscode_dir / "settings.json"
    
    settings = {
        "python.linting.enabled": True,
        "python.linting.ruffEnabled": True,
        "python.formatting.provider": "black",
        "editor.formatOnSave": True,
        "editor.codeActionsOnSave": {
            "source.organizeImports": "explicit"
        },
        "[python]": {
            "editor.defaultFormatter": "ms-python.black-formatter",
            "editor.codeActionsOnSave": {
                "source.organizeImports": "explicit"
            }
        }
    }
    
    import json
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=4)
    
    print(f"Created VS Code settings at {settings_path}")

def main():
    """Main entry point to configure linting and formatting."""
    print("Configuring linting (ruff) and formatting (black)...")
    
    ensure_requirements()
    create_ruff_config()
    create_black_config()
    create_vscode_settings()
    
    print("\nConfiguration complete!")
    print("\nTo run linter: ruff check .")
    print("To format code: black .")
    print("To fix linting issues automatically: ruff check --fix .")

if __name__ == "__main__":
    main()