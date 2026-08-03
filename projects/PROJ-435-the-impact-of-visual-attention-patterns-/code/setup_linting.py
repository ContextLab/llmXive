"""
Setup script to initialize linting (Ruff) and formatting (Black) configurations.
This script ensures the necessary configuration files exist in the code/ directory.
"""
import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd: list, description: str) -> bool:
    """Run a shell command and report status."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"  Success: {description}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  Failed: {description}")
        print(f"  Error: {e.stderr}")
        return False

def create_ruff_config() -> bool:
    """Create .ruff.toml configuration file."""
    config_path = Path("code/.ruff.toml")
    if config_path.exists():
        print(f"  Config already exists: {config_path}")
        return True

    content = """
[lint]
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
    "B008", # do not perform function calls in argument defaults (common in data pipelines)
]

[lint.per-file-ignores]
"__init__.py" = ["F401"] # Allow unused imports in init files for API exposure

[format]
# Black-compatible settings
line-length = 88
indent-width = 4
"""
    try:
        config_path.write_text(content.strip())
        print(f"  Created: {config_path}")
        return True
    except Exception as e:
        print(f"  Failed to create {config_path}: {e}")
        return False

def create_black_config() -> bool:
    """Create .black.toml configuration file."""
    config_path = Path("code/.black.toml")
    if config_path.exists():
        print(f"  Config already exists: {config_path}")
        return True

    content = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
extend-exclude = '''
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
    try:
        config_path.write_text(content.strip())
        print(f"  Created: {config_path}")
        return True
    except Exception as e:
        print(f"  Failed to create {config_path}: {e}")
        return False

def main():
    """Main entry point for setup_linting."""
    print("Setting up linting and formatting tools...")

    # Ensure we are in the project root or code directory
    if not Path("code").exists():
        print("Error: 'code' directory not found. Run from project root.")
        return 1

    # Change to code directory for config creation
    os.chdir("code")

    success = True

    # Create configuration files
    if not create_ruff_config():
        success = False
    if not create_black_config():
        success = False

    # Verify installations
    print("\nChecking tool installations...")
    if not run_command([sys.executable, "-m", "pip", "install", "ruff", "black"],
                       "Installing ruff and black"):
        success = False

    # Run initial lint check (non-strict, just to verify setup)
    if success:
        print("\nVerifying configuration...")
        run_command([sys.executable, "-m", "ruff", "check", "."],
                    "Running ruff check (verification)")
        run_command([sys.executable, "-m", "black", "--check", "."],
                    "Running black check (verification)")

    if success:
        print("\nSetup complete. Linting and formatting tools are configured.")
    else:
        print("\nSetup completed with warnings. Please check the output above.")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())