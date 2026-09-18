import subprocess
import sys
import os
from pathlib import Path
from config import PROJECT_ROOT

def get_black_config_path() -> Path:
    """Return the path to the black configuration file."""
    return PROJECT_ROOT / "pyproject.toml"

def get_flake8_config_path() -> Path:
    """Return the path to the flake8 configuration file."""
    return PROJECT_ROOT / ".flake8"

def setup_black_config() -> None:
    """Create or update pyproject.toml with black configuration."""
    config_path = get_black_config_path()
    config_content = """[tool.black]
line-length = 88
target-version = ['py310']
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
)/
'''
"""
    with open(config_path, "w") as f:
        f.write(config_content)
    print(f"Black configuration created at {config_path}")

def setup_flake8_config() -> None:
    """Create or update .flake8 with flake8 configuration."""
    config_path = get_flake8_config_path()
    config_content = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    build,
    dist,
    .tox,
    .venv
per-file-ignores =
    __init__.py: F401
"""
    with open(config_path, "w") as f:
        f.write(config_content)
    print(f"Flake8 configuration created at {config_path}")

def install_tools() -> None:
    """Install black and flake8 if not already installed."""
    tools = ["black", "flake8"]
    for tool in tools:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", tool])
            print(f"{tool} installed successfully.")
        except subprocess.CalledProcessError:
            print(f"Failed to install {tool}. Please install it manually.")
            sys.exit(1)

def run_formatting() -> None:
    """Run black formatting on the code directory."""
    code_dir = PROJECT_ROOT / "code"
    try:
        subprocess.check_call(["black", str(code_dir)])
        print("Formatting completed successfully.")
    except subprocess.CalledProcessError:
        print("Formatting failed. Please check the code for errors.")
        sys.exit(1)

def run_linting() -> None:
    """Run flake8 linting on the code directory."""
    code_dir = PROJECT_ROOT / "code"
    try:
        subprocess.check_call(["flake8", str(code_dir)])
        print("Linting completed successfully.")
    except subprocess.CalledProcessError:
        print("Linting failed. Please fix the reported issues.")
        sys.exit(1)

def main() -> None:
    """Main function to set up and run linting and formatting."""
    print("Setting up linting and formatting tools...")
    install_tools()
    setup_black_config()
    setup_flake8_config()
    print("\nRunning formatting...")
    run_formatting()
    print("\nRunning linting...")
    run_linting()
    print("\nAll tasks completed.")

if __name__ == "__main__":
    main()