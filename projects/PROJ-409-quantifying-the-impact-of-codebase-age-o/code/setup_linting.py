import os
import subprocess
import sys
from pathlib import Path

def ensure_requirements_updated():
    """Ensure ruff and black are listed in requirements.txt."""
    requirements_path = Path("requirements.txt")
    if not requirements_path.exists():
        print("requirements.txt not found. Creating it...")
        requirements_path.write_text("# Project dependencies\n")

    content = requirements_path.read_text()
    missing = []
    if "ruff" not in content:
        missing.append("ruff")
    if "black" not in content:
        missing.append("black")

    if missing:
        with requirements_path.open("a") as f:
            for pkg in missing:
                f.write(f"{pkg}\n")
        print(f"Added missing dependencies to requirements.txt: {missing}")
    else:
        print("requirements.txt already contains ruff and black.")

def create_ruff_config():
    """Create a ruff.toml configuration file."""
    config_path = Path("ruff.toml")
    if config_path.exists():
        print("ruff.toml already exists. Skipping creation.")
        return

    config_content = """# Ruff configuration for llmXive project

# Target Python version
target-version = "py311"

# Line length
line-length = 88

# Exclude directories
exclude = [
    ".git",
    "__pycache__",
    ".eggs",
    "*.egg-info",
    "build",
    "dist",
    ".venv",
    "venv",
]

[lint]
# Select specific rules
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
]

# Ignore specific rules if needed
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
]

# Allow autofix for all enabled rules
fixable = ["ALL"]
unfixable = []

[lint.per-file-ignores]
"__init__.py" = ["F401"]  # Ignore unused imports in init files

[lint.isort]
known-first-party = ["utils", "extraction", "inference", "analysis", "models"]
"""
    config_path.write_text(config_content)
    print(f"Created ruff configuration at {config_path}")

def create_black_config():
    """Create a pyproject.toml with Black configuration if not present."""
    config_path = Path("pyproject.toml")
    
    content = ""
    if config_path.exists():
        content = config_path.read_text()
        # Check if [tool.black] section already exists
        if "[tool.black]" in content:
            print("Black configuration already exists in pyproject.toml.")
            return
    
    # Append Black configuration
    black_section = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''
"""
    
    if config_path.exists():
        with config_path.open("a") as f:
            f.write(black_section)
    else:
        config_path.write_text(black_section)
        
    print(f"Updated Black configuration at {config_path}")

def install_tools():
    """Install ruff and black using pip."""
    print("Installing linting and formatting tools...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ruff", "black"])
        print("Successfully installed ruff and black.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing tools: {e}")
        sys.exit(1)

def main():
    """Main entry point for setting up linting and formatting."""
    print("Setting up linting (ruff) and formatting (black) tools...")
    
    # Step 1: Install tools
    install_tools()
    
    # Step 2: Update requirements.txt
    ensure_requirements_updated()
    
    # Step 3: Create configuration files
    create_ruff_config()
    create_black_config()
    
    print("Linting and formatting setup complete!")
    print("\nYou can now run:")
    print("  ruff check .        # Check for linting issues")
    print("  ruff check --fix .  # Automatically fix fixable issues")
    print("  black .             # Format code with Black")

if __name__ == "__main__":
    main()