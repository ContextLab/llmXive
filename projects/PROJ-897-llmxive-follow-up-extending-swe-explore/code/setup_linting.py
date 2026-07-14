"""
Setup script to configure linting (ruff) and formatting (black) tools.

This script generates configuration files for the project:
- .ruff.toml: Linting configuration
- .flake8: Flaked8 configuration (if needed, though ruff replaces it)
- pyproject.toml: Black formatting configuration

It also updates requirements.txt with necessary dependencies.
"""
import os
import sys
from pathlib import Path

def ensure_requirements():
    """Ensure linting and formatting dependencies are in requirements.txt."""
    requirements_path = Path("requirements.txt")
    required_packages = [
        "ruff>=0.1.0",
        "black>=23.0.0",
        "pytest>=7.0.0",
        "pyyaml>=6.0",
    ]
    
    existing_packages = set()
    if requirements_path.exists():
        with open(requirements_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Extract package name (before any version specifier)
                    pkg_name = line.split(">=")[0].split("<=")[0].split("==")[0].split("[")[0].strip()
                    existing_packages.add(pkg_name.lower())
    
    new_packages = []
    for pkg in required_packages:
        pkg_name = pkg.split(">=")[0].split("<=")[0].split("==")[0].split("[")[0].strip().lower()
        if pkg_name not in existing_packages:
            new_packages.append(pkg)
    
    if new_packages:
        with open(requirements_path, "a", encoding="utf-8") as f:
            f.write("\n")
            for pkg in new_packages:
                f.write(f"{pkg}\n")
        print(f"Added to requirements.txt: {', '.join(new_packages)}")
    else:
        print("All linting/formatting dependencies already in requirements.txt")

def create_ruff_config():
    """Create .ruff.toml configuration file."""
    config_content = """[lint]
# Enable all rules from the recommended set
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
    "UP", # pyupgrade
    "SIM",# flake8-simplify
    "ARG",# flake8-unused-arguments
]

# Ignore specific rules that conflict with project style
ignore = [
    "E501", # Line too long (handled by black)
    "B008", # Do not perform function call in argument defaults (common in tests)
    "ARG001", # Unused function argument (sometimes intentional in interfaces)
]

# Allow autofix for all enabled rules
fixable = ["ALL"]
unfixable = []

# Exclude directories
exclude = [
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".eggs",
    "*.egg",
    "*.egg-info",
    "build",
    "dist",
]

[lint.per-file-ignores]
# Allow unused imports in __init__.py for public API exposure
"__init__.py" = ["F401"]

[lint.isort]
# Configuration for import sorting
known-first-party = ["code", "tests"]
force-single-line = false
lines-after-imports = 2

[format]
# Configuration for formatting (if using ruff format)
quote-style = "double"
indent-style = "space"
line-ending = "auto"
"""
    config_path = Path(".ruff.toml")
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(config_content)
    print(f"Created {config_path}")

def create_black_config():
    """Create pyproject.toml with Black configuration."""
    # Check if pyproject.toml exists
    pyproject_path = Path("pyproject.toml")
    
    if pyproject_path.exists():
        with open(pyproject_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check if [tool.black] section already exists
        if "[tool.black]" in content:
            print("Black configuration already exists in pyproject.toml")
            return
    
    config_section = """
[tool.black]
line-length = 88
target-version = ['py310']
include = '\\.pyi?$'
extend-exclude = '''
(
  .venv
  | venv
  | env
  | __pycache__
  | .git
  | .eggs
  | *.egg
  | *.egg-info
  | build
  | dist
)
'''
"""
    
    if pyproject_path.exists():
        with open(pyproject_path, "a", encoding="utf-8") as f:
            f.write(config_section)
        print(f"Added Black configuration to {pyproject_path}")
    else:
        with open(pyproject_path, "w", encoding="utf-8") as f:
            f.write("[project]\nname = \"llmxive\"\nversion = \"0.1.0\"\n")
            f.write(config_section)
        print(f"Created {pyproject_path} with Black configuration")

def create_flake8_config():
    """Create .flake8 configuration file (optional, for compatibility)."""
    # Ruff can replace flake8, but we create a minimal config for compatibility
    config_content = """[flake8]
max-line-length = 88
exclude = 
    .git,
    __pycache__,
    .venv,
    venv,
    env,
    .eggs,
    *.egg,
    *.egg-info,
    build,
    dist
ignore = E501,B008
"""
    config_path = Path(".flake8")
    # Only create if it doesn't exist
    if not config_path.exists():
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(config_content)
        print(f"Created {config_path}")
    else:
        print(f"{config_path} already exists")

def main():
    """Main entry point for setup script."""
    print("Setting up linting and formatting tools...")
    
    # Ensure we're in the project root
    if not Path("code").exists() or not Path("data").exists():
        print("Error: Please run this script from the project root directory.")
        sys.exit(1)
    
    ensure_requirements()
    create_ruff_config()
    create_black_config()
    create_flake8_config()
    
    print("\nLinting and formatting setup complete!")
    print("\nTo use the tools:")
    print("  Format code: black code/ tests/")
    print("  Lint code: ruff check code/ tests/")
    print("  Format and lint: black code/ tests/ && ruff check code/ tests/")

if __name__ == "__main__":
    main()