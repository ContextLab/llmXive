import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Optional

def check_command_available(command: str) -> bool:
    """Check if a command-line tool is available in the system PATH."""
    try:
        subprocess.run([command, "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def create_pyproject_config(root: Path) -> Path:
    """Create or update pyproject.toml with ruff and black configuration."""
    pyproject_path = root / "pyproject.toml"
    
    config_content = """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "llmxive-material-stiffness"
version = "0.1.0"
description = "Predicting Material Stiffness from Microstructure Images Using CNNs"
requires-python = ">=3.10"

[tool.black]
line-length = 88
target-version = ['py310']
include = '\\.pyi?$'
exclude = '''
/(
    \\.git
  | \\.mypy_cache
  | \\.tox
  | \\.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''

[tool.ruff]
# Enable pycodestyle (`E`), Pyflakes (`F`), and isort (`I`)
# W: pycodestyle warnings
# N: pep8-naming
select = ["E", "F", "W", "I", "N"]
ignore = []

# Allow autofix for all enabled rules (when `--fix` is provided)
fixable = ["ALL"]
unfixable = []

# Exclude a few specific directories
extend-exclude = [
    "__pycache__",
    ".git",
    ".mypy_cache",
    ".venv",
    "build",
    "dist",
]

# Same as Black.
line-length = 88

[tool.ruff.isort]
known-first-party = ["code"]
"""
    
    pyproject_path.write_text(config_content)
    return pyproject_path

def validate_config_files(root: Path) -> Tuple[bool, List[str]]:
    """Verify that ruff and black configurations are valid."""
    errors = []
    
    # Check pyproject.toml exists
    pyproject_path = root / "pyproject.toml"
    if not pyproject_path.exists():
        errors.append("pyproject.toml not found")
        return False, errors
    
    # Try to parse it
    try:
        import tomllib
        with open(pyproject_path, "rb") as f:
            tomllib.load(f)
    except Exception as e:
        errors.append(f"Invalid TOML in pyproject.toml: {e}")
        return False, errors
    
    return True, errors

def main() -> int:
    """Main entry point for the linting setup script."""
    root = Path(__file__).resolve().parent.parent.parent
    
    print("Setting up linting and formatting configuration...")
    
    # Create pyproject.toml
    config_path = create_pyproject_config(root)
    print(f"Created/updated configuration at: {config_path}")
    
    # Validate configuration
    is_valid, errors = validate_config_files(root)
    if not is_valid:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    
    print("Configuration validation passed.")
    
    # Check if tools are available
    ruff_available = check_command_available("ruff")
    black_available = check_command_available("black")
    
    if not ruff_available:
        print("WARNING: ruff is not installed. Install with: pip install ruff")
    else:
        print("ruff is available.")
    
    if not black_available:
        print("WARNING: black is not installed. Install with: pip install black")
    else:
        print("black is available.")
    
    # Run checks if tools are available
    if ruff_available:
        print("Running ruff check...")
        result = subprocess.run(["ruff", "check", "."], cwd=root)
        if result.returncode != 0:
            print("ruff check found issues (this is expected if code is not yet compliant).")
        else:
            print("ruff check passed.")
    
    if black_available:
        print("Running black --check...")
        result = subprocess.run(["black", "--check", "."], cwd=root)
        if result.returncode != 0:
            print("black --check found issues (this is expected if code is not yet formatted).")
        else:
            print("black --check passed.")
    
    print("Linting configuration setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())