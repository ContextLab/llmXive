import subprocess
import sys
import os
from pathlib import Path

def ensure_package_installed(package_name: str, pip_name: str = None) -> None:
    """Check if a package is installed, install it if not."""
    if pip_name is None:
        pip_name = package_name
    
    try:
        __import__(package_name.replace('-', '_'))
    except ImportError:
        print(f"Installing {pip_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
        print(f"{pip_name} installed successfully.")

def create_ruff_config() -> None:
    """Create a default ruff.toml configuration file."""
    config_content = """# Ruff configuration for llmXive project
[lint]
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
"tests/*" = ["S101"] # assert allowed in tests

[lint.isort]
known-first-party = ["src"]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    path = Path("ruff.toml")
    if not path.exists():
        path.write_text(config_content)
        print("Created ruff.toml")
    else:
        print("ruff.toml already exists")

def create_pyproject_config() -> None:
    """Create a pyproject.toml with black configuration."""
    config_content = """[tool.black]
line-length = 88
target-version = ['py311']
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

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
"""
    path = Path("pyproject.toml")
    if not path.exists():
        path.write_text(config_content)
        print("Created pyproject.toml")
    else:
        print("pyproject.toml already exists")

def main() -> None:
    """Main entry point for configuring linting and formatting."""
    print("Configuring linting (ruff) and formatting (black)...")
    
    # Ensure packages are installed
    ensure_package_installed("ruff", "ruff")
    ensure_package_installed("black", "black")
    
    # Verify installation
    try:
        ruff_result = subprocess.run(
            [sys.executable, "-m", "ruff", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Ruff version: {ruff_result.stdout.strip()}")
    except subprocess.CalledProcessError:
        print("ERROR: ruff installation verification failed")
        sys.exit(1)
    
    try:
        black_result = subprocess.run(
            [sys.executable, "-m", "black", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Black version: {black_result.stdout.strip()}")
    except subprocess.CalledProcessError:
        print("ERROR: black installation verification failed")
        sys.exit(1)
    
    # Create configuration files
    create_ruff_config()
    create_pyproject_config()
    
    # Run checks (these may fail if code is not formatted yet, which is expected)
    print("\nRunning initial checks...")
    try:
        subprocess.run(
            [sys.executable, "-m", "ruff", "check", "."],
            check=False
        )
    except Exception as e:
        print(f"Ruff check completed (may have linting errors): {e}")
    
    try:
        subprocess.run(
            [sys.executable, "-m", "black", "--check", "."],
            check=False
        )
    except Exception as e:
        print(f"Black check completed (may have formatting errors): {e}")
    
    print("\nLinting and formatting configuration complete.")

if __name__ == "__main__":
    main()