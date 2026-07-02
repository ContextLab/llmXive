"""
Linting and Formatting Configuration for llmXive Project.

This module provides configuration constants and setup logic for:
- Black: Code formatting
- Flake8: Code linting
- isort: Import sorting (optional, aligned with black)

Usage:
    Run 'python -m linting_config' to install and configure tools.
    Or import and use configuration dictionaries in CI/CD scripts.
"""

import subprocess
import sys
import os

# Configuration constants matching project requirements
BLACK_CONFIG = {
    "line_length": 88,
    "target_version": ["py311"],
    "skip_string_normalization": False,
    "exclude": r'\.git|__pycache__|\.eggs|build|dist',
}

FLAKE8_CONFIG = {
    "max-line-length": 88,
    "extend-ignore": "E203,W503",  # Compatible with Black
    "exclude": ".git,__pycache__,.eggs,build,dist",
    "per-file-ignores": {
        "__init__.py": "F401",  # Allow unused imports in __init__.py
    },
    "max-complexity": 10,
}

ISORT_CONFIG = {
    "profile": "black",
    "line_length": 88,
    "skip": [".git", "__pycache__", ".eggs", "build", "dist"],
}

def get_black_config_path():
    """Return the path to the pyproject.toml for Black configuration."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "pyproject.toml")

def get_flake8_config_path():
    """Return the path to the .flake8 config file."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, ".flake8")

def setup_black_config():
    """Write Black configuration to pyproject.toml."""
    config_path = get_black_config_path()
    content = f"""[tool.black]
line-length = {BLACK_CONFIG['line_length']}
target-version = {BLACK_CONFIG['target_version']}
skip-string-normalization = {BLACK_CONFIG['skip_string_normalization']}
exclude = '{BLACK_CONFIG['exclude']}'
"""
    with open(config_path, "w") as f:
        f.write(content)
    print(f"Black configuration written to {config_path}")

def setup_flake8_config():
    """Write Flake8 configuration to .flake8."""
    config_path = get_flake8_config_path()
    content = f"""[flake8]
max-line-length = {FLAKE8_CONFIG['max-line-length']}
extend-ignore = {FLAKE8_CONFIG['extend-ignore']}
exclude = {FLAKE8_CONFIG['exclude']}
max-complexity = {FLAKE8_CONFIG['max-complexity']}
per-file-ignores = {FLAKE8_CONFIG['per-file-ignores']}
"""
    with open(config_path, "w") as f:
        f.write(content)
    print(f"Flake8 configuration written to {config_path}")

def install_tools():
    """Install Black and Flake8 if not already installed."""
    tools = ["black", "flake8"]
    for tool in tools:
        try:
            __import__(tool.replace("-", "_"))
            print(f"{tool} is already installed.")
        except ImportError:
            print(f"Installing {tool}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", tool])

def run_formatting():
    """Run Black on the code directory."""
    code_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code")
    if os.path.exists(code_dir):
        print(f"Running Black on {code_dir}...")
        subprocess.check_call(["black", code_dir])
    else:
        print(f"Directory {code_dir} does not exist. Skipping formatting.")

def run_linting():
    """Run Flake8 on the code directory."""
    code_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code")
    if os.path.exists(code_dir):
        print(f"Running Flake8 on {code_dir}...")
        subprocess.check_call(["flake8", code_dir])
    else:
        print(f"Directory {code_dir} does not exist. Skipping linting.")

def main():
    """Main entry point for setup and execution."""
    print("Configuring linting and formatting tools...")
    install_tools()
    setup_black_config()
    setup_flake8_config()
    print("Configuration complete.")
    print("\nTo format code: python -m linting_config --format")
    print("To lint code: python -m linting_config --lint")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Linting and Formatting Configuration")
    parser.add_argument("--format", action="store_true", help="Run Black formatter")
    parser.add_argument("--lint", action="store_true", help="Run Flake8 linter")
    args = parser.parse_args()

    if args.format:
        run_formatting()
    elif args.lint:
        run_linting()
    else:
        main()