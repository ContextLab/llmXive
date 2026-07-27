"""
Setup script for linting and formatting tools (T001b).
This script ensures the necessary configuration files exist
and can be used to install dev dependencies if needed.
"""
import os
import sys
from pathlib import Path
import subprocess

def ensure_requirements():
    """Check if dev requirements are installed."""
    try:
        import ruff
        import black
        import flake8
        print("✓ Linting dependencies (ruff, black, flake8) are installed.")
        return True
    except ImportError:
        print("⚠ Linting dependencies not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", ".[dev]"])
            print("✓ Dependencies installed successfully.")
            return True
        except subprocess.CalledProcessError:
            print("✗ Failed to install dependencies. Please install manually: pip install -e '.[dev]'")
            return False

def create_ruff_config():
    """Ensure .ruff.toml exists."""
    ruff_config = Path("code/.ruff.toml")
    if not ruff_config.exists():
        print("⚠ .ruff.toml not found. Creating default...")
        ruff_config.write_text("""
[lint]
select = ["E", "W", "F", "I", "B", "C4", "UP"]
ignore = ["E501", "B008", "C408"]

[lint.per-file-ignores]
"__init__.py" = ["F401"]
""")
    else:
        print("✓ .ruff.toml exists.")

def create_black_config():
    """Ensure .black.toml exists."""
    black_config = Path("code/.black.toml")
    if not black_config.exists():
        print("⚠ .black.toml not found. Creating default...")
        black_config.write_text("""
[tool.black]
line-length = 88
target-version = ['py310']
""")
    else:
        print("✓ .black.toml exists.")

def create_flake8_config():
    """Ensure .flake8 exists (legacy compatibility)."""
    flake8_config = Path("code/.flake8")
    if not flake8_config.exists():
        print("⚠ .flake8 not found. Creating default...")
        flake8_config.write_text("""
[flake8]
max-line-length = 88
ignore = E501, W503
exclude = .git,__pycache__,build,dist
""")
    else:
        print("✓ .flake8 exists.")

def main():
    """Main entry point for T001b setup."""
    print("Running T001b: Configure Linting and Formatting...")
    
    if not ensure_requirements():
        print("⚠ Cannot proceed without dependencies.")
        return 1

    create_ruff_config()
    create_black_config()
    create_flake8_config()

    print("✓ T001b configuration complete.")
    print("  Run 'ruff check code/' and 'black --check code/' to verify.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
