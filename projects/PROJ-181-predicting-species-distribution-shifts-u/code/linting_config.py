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
    black_config = """
[tool.black]
line-length = 88
target-version = ['py310']
include = '\\.pyi?$'
exclude = '''
/(
    \\.eggs
  | \\.git
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
    # Check if file exists and has [tool.black] section
    if config_path.exists():
        content = config_path.read_text()
        if "[tool.black]" in content:
            print("Black configuration already exists.")
            return

    with open(config_path, "w") as f:
        f.write(black_config)
    print(f"Black configuration written to {config_path}")

def setup_flake8_config() -> None:
    """Create .flake8 configuration file."""
    config_path = get_flake8_config_path()
    flake8_config = """
[flake8]
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
    # Allow unused imports in __init__.py
    */__init__.py:F401
"""
    with open(config_path, "w") as f:
        f.write(flake8_config)
    print(f"Flake8 configuration written to {config_path}")

def install_tools() -> None:
    """Install black and flake8 if not already installed."""
    tools = ["black", "flake8"]
    for tool in tools:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", tool])
            print(f"{tool} installed successfully.")
        except subprocess.CalledProcessError:
            print(f"Failed to install {tool}. Please install manually.")

def run_formatting() -> None:
    """Run black formatter on the codebase."""
    try:
        subprocess.check_call(
            [sys.executable, "-m", "black", str(PROJECT_ROOT / "code")]
        )
        print("Formatting completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Formatting failed: {e}")
        raise

def run_linting() -> None:
    """Run flake8 linter on the codebase."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", str(PROJECT_ROOT / "code")],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("No linting issues found.")
        else:
            print("Linting issues found:")
            print(result.stdout)
            print(result.stderr)
            raise SystemExit(1)
    except subprocess.CalledProcessError as e:
        print(f"Linting failed: {e}")
        raise

def main() -> None:
    """Main entry point for linting configuration and execution."""
    print("Setting up linting tools...")
    install_tools()
    setup_black_config()
    setup_flake8_config()

    print("\nRunning formatter...")
    try:
        run_formatting()
    except SystemExit:
        print("Formatting encountered errors. Please fix them.")
        return

    print("\nRunning linter...")
    try:
        run_linting()
    except SystemExit:
        print("Linting encountered errors. Please fix them.")
        return

    print("\nAll linting checks passed!")

if __name__ == "__main__":
    main()