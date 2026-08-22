"""
Setup script for linting (Ruff) and formatting (Black) tools.
This script ensures configuration files exist and provides a verification step.
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """Run a shell command and report status."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}: {e}")
        if e.stderr:
            print(e.stderr)
        return False

def check_config_files() -> bool:
    """Verify that configuration files exist in the code directory."""
    code_dir = Path(__file__).parent
    config_files = [
        code_dir / ".ruff.toml",
        code_dir / "pyproject.toml",
    ]

    all_exist = True
    for f in config_files:
        if not f.exists():
            print(f"Missing config file: {f}")
            all_exist = False
        else:
            print(f"Found config file: {f}")

    return all_exist

def create_ruff_config() -> None:
    """Create .ruff.toml if it doesn't exist."""
    code_dir = Path(__file__).parent
    config_path = code_dir / ".ruff.toml"
    if not config_path.exists():
        content = """[lint]
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

[lint.per-file-ignores]
"__init__.py" = ["F401"] # allow unused imports in init files

[format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"
"""
        config_path.write_text(content)
        print(f"Created {config_path}")
    else:
        print(f"{config_path} already exists, skipping creation.")

def create_black_config() -> None:
    """Ensure Black config exists in pyproject.toml."""
    code_dir = Path(__file__).parent
    config_path = code_dir / "pyproject.toml"
    if not config_path.exists():
        # Minimal creation if missing, though T002 should have handled requirements
        content = """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "llmxive-antibiotic-resistance"
version = "0.1.0"
requires-python = ">=3.11"

[tool.black]
line-length = 88
target-version = ['py311']
"""
        config_path.write_text(content)
        print(f"Created {config_path}")
    else:
        # Check if [tool.black] exists
        text = config_path.read_text()
        if "[tool.black]" not in text:
            # Append black config
            black_config = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
"""
            config_path.write_text(text + black_config)
            print(f"Appended Black config to {config_path}")
        else:
            print(f"{config_path} already contains Black config.")

def main() -> int:
    """Main entry point."""
    print("=== Setting up Linting and Formatting Tools ===")

    # Ensure config files exist
    create_ruff_config()
    create_black_config()

    if not check_config_files():
        print("Error: Missing configuration files.")
        return 1

    # Verify tools are installed
    tools = [
        (["ruff", "--version"], "Ruff installed"),
        (["black", "--version"], "Black installed"),
    ]

    all_ok = True
    for cmd, desc in tools:
        if not run_command(cmd, desc):
            print(f"Warning: {desc} failed. Install with: pip install ruff black")
            all_ok = False

    if all_ok:
        print("\n=== Linting and Formatting tools configured successfully ===")
        print("Run 'ruff check . --fix' to lint and fix issues.")
        print("Run 'black .' to format code.")
    else:
        print("\n=== Some tools are missing. Please install them. ===")

    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())