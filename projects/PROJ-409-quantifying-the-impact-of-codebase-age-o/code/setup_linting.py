"""
Script to configure linting (ruff) and formatting (black) tools for the project.
This script updates requirements.txt, creates configuration files, and installs tools.
"""
import os
import subprocess
import sys
from pathlib import Path

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"
PYPROJECT_FILE = PROJECT_ROOT / "pyproject.toml"
RUFF_CONFIG_FILE = PROJECT_ROOT / "ruff.toml"

def ensure_requirements_updated():
    """Ensure ruff and black are present in requirements.txt."""
    if not REQUIREMENTS_FILE.exists():
        print(f"Error: {REQUIREMENTS_FILE} not found. Run T002 first.")
        sys.exit(1)

    content = REQUIREMENTS_FILE.read_text()
    lines = content.splitlines()
    new_lines = []
    added_ruff = False
    added_black = False

    for line in lines:
        new_lines.append(line)
        stripped = line.strip().lower()
        if stripped.startswith("ruff"):
            added_ruff = True
        elif stripped.startswith("black"):
            added_black = True

    if not added_ruff:
        new_lines.append("ruff>=0.1.0")
        print("Added 'ruff>=0.1.0' to requirements.txt")

    if not added_black:
        new_lines.append("black>=23.0.0")
        print("Added 'black>=23.0.0' to requirements.txt")

    new_content = "\n".join(new_lines) + "\n"
    REQUIREMENTS_FILE.write_text(new_content)
    print("Updated requirements.txt")

def create_ruff_config():
    """Create ruff.toml configuration file."""
    config_content = """# Ruff configuration for llmXive project
target-version = "py311"
line-length = 88
exclude = [
    ".git",
    "__pycache__",
    ".eggs",
    "*.egg-info",
    "build",
    "dist",
    "venv",
    ".venv",
    "data",
]

[lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "UP",   # pyupgrade
    "N",    # pep8-naming
    "SIM",  # flake8-simplify
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
]

[lint.per-file-ignores]
"__init__.py" = ["F401"]

[lint.isort]
known-first-party = ["utils", "extraction", "inference", "analysis", "models"]
force-single-line = true
lines-between-types = 1

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    RUFF_CONFIG_FILE.write_text(config_content)
    print(f"Created {RUFF_CONFIG_FILE}")

def create_black_config():
    """Create Black configuration in pyproject.toml."""
    # Read existing pyproject.toml if it exists
    if PYPROJECT_FILE.exists():
        content = PYPROJECT_FILE.read_text()
        # Check if [tool.black] section already exists
        if "[tool.black]" in content:
            print(f"[tool.black] section already exists in {PYPROJECT_FILE}")
            return
    else:
        content = ""

    black_section = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \.git
  | \.eggs
  | \.mypy_cache
  | \.venv
  | venv
  | build
  | dist
  | data
)/
'''
"""
    if content and not content.endswith("\n"):
        content += "\n"
    content += black_section
    PYPROJECT_FILE.write_text(content)
    print(f"Updated {PYPROJECT_FILE} with Black configuration")

def install_tools():
    """Install ruff and black."""
    print("Installing linting and formatting tools...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)])
        print("Tools installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing tools: {e}")
        sys.exit(1)

def main():
    """Main entry point for setup_linting."""
    print("Setting up linting and formatting tools...")
    ensure_requirements_updated()
    create_ruff_config()
    create_black_config()
    install_tools()
    print("Linting and formatting setup complete.")
    print("\nTo use:")
    print("  Format code: black code/")
    print("  Check format: black --check code/")
    print("  Lint code: ruff check code/")
    print("  Fix lint issues: ruff check --fix code/")

if __name__ == "__main__":
    main()