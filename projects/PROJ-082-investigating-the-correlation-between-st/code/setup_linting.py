"""
Setup script for linting (ruff) and formatting (black) tools.
This script installs the tools, creates configuration files, and provides
utility functions to run lint and format checks.
"""
import subprocess
import sys
from pathlib import Path
import json

# Configuration for the project
RUFF_CONFIG_NAME = ".ruff.toml"
BLACK_CONFIG_NAME = "pyproject.toml"  # Black settings go in pyproject.toml usually, or .black.toml
# We will create a minimal pyproject.toml if it doesn't exist, or append to it.
# For simplicity in this task, we create a dedicated config file for Black if preferred,
# but standard practice is pyproject.toml. Let's stick to creating .ruff.toml and ensuring pyproject.toml has black config.

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent

def install_tools() -> bool:
    """Install ruff and black using pip."""
    tools = ["ruff", "black"]
    for tool in tools:
        try:
            print(f"Checking if {tool} is installed...")
            subprocess.run([sys.executable, "-m", "pip", "show", tool], check=True, capture_output=True)
            print(f"{tool} is already installed.")
        except subprocess.CalledProcessError:
            print(f"Installing {tool}...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", tool],
                check=True,
                capture_output=False
            )
            if result.returncode == 0:
                print(f"{tool} installed successfully.")
            else:
                print(f"Failed to install {tool}.")
                return False
    return True

def ensure_config_file() -> bool:
    """Create .ruff.toml and ensure pyproject.toml has black configuration."""
    project_root = get_project_root()
    ruff_config_path = project_root / RUFF_CONFIG_NAME
    black_config_path = project_root / "pyproject.toml"

    # Create .ruff.toml
    if not ruff_config_path.exists():
        print(f"Creating {RUFF_CONFIG_NAME}...")
        ruff_content = """[lint]
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
"__init__.py" = ["F401"]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
        with open(ruff_config_path, "w") as f:
            f.write(ruff_content)
        print(f"{RUFF_CONFIG_NAME} created.")
    else:
        print(f"{RUFF_CONFIG_NAME} already exists.")

    # Ensure pyproject.toml has black configuration
    black_config_section = """
[tool.black]
line-length = 88
target-version = ['py311']
"""
    if black_config_path.exists():
        with open(black_config_path, "r") as f:
            content = f.read()
        if "[tool.black]" not in content:
            print(f"Appending Black configuration to {BLACK_CONFIG_NAME}...")
            with open(black_config_path, "a") as f:
                f.write(black_config_section)
        else:
            print(f"Black configuration already exists in {BLACK_CONFIG_NAME}.")
    else:
        print(f"Creating {BLACK_CONFIG_NAME} with Black configuration...")
        with open(black_config_path, "w") as f:
            f.write(black_config_section)

    return True

def run_lint_check() -> int:
    """Run ruff check on the codebase."""
    project_root = get_project_root()
    code_dir = project_root / "code"
    if not code_dir.exists():
        print("Code directory not found. Nothing to lint.")
        return 0

    print("Running ruff check...")
    try:
        result = subprocess.run(
            ["ruff", "check", str(code_dir)],
            cwd=project_root,
            capture_output=False,
            text=True
        )
        return result.returncode
    except FileNotFoundError:
        print("ruff not found. Please install it.")
        return 1

def run_format_check() -> int:
    """Run black check (diff mode) on the codebase."""
    project_root = get_project_root()
    code_dir = project_root / "code"
    if not code_dir.exists():
        print("Code directory not found. Nothing to format check.")
        return 0

    print("Running black --check...")
    try:
        result = subprocess.run(
            ["black", "--check", str(code_dir)],
            cwd=project_root,
            capture_output=False,
            text=True
        )
        return result.returncode
    except FileNotFoundError:
        print("black not found. Please install it.")
        return 1

def main():
    """Main entry point for setup_linting."""
    print("Setting up linting and formatting tools...")

    # Step 1: Install tools
    if not install_tools():
        print("Failed to install tools. Exiting.")
        sys.exit(1)

    # Step 2: Ensure config files exist
    if not ensure_config_file():
        print("Failed to create config files. Exiting.")
        sys.exit(1)

    print("Setup complete. You can now run 'python code/setup_linting.py run' to lint and format.")

if __name__ == "__main__":
    main()