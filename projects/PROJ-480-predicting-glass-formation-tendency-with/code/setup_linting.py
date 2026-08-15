"""
Setup script to configure linting (ruff) and formatting (black) tools.
This script creates configuration files and installs necessary dependencies.
"""
import os
import sys
from pathlib import Path

def create_pyproject_config():
    """Create or update pyproject.toml with black and ruff configurations."""
    pyproject_path = Path("pyproject.toml")
    
    if not pyproject_path.exists():
        print("Error: pyproject.toml not found. Run T002 first.")
        sys.exit(1)
    
    # Read existing content
    content = pyproject_path.read_text()
    
    # Check if tool sections already exist
    has_black = "[tool.black]" in content
    has_ruff = "[tool.ruff]" in content
    
    new_sections = []
    
    if not has_black:
        new_sections.append("""
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
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
""")
    
    if not has_ruff:
        new_sections.append("""
[tool.ruff]
line-length = 88
target-version = "py311"
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
    "C901", # too complex
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]

[tool.ruff.isort]
known-first-party = ["src", "tests", "data", "models", "reports", "cli", "lib"]
force-single-line = false
""")
    
    if new_sections:
        # Append new sections
        with open(pyproject_path, "a") as f:
            for section in new_sections:
                f.write(section)
        print("Updated pyproject.toml with linting and formatting configurations.")
    else:
        print("Linting and formatting configurations already present in pyproject.toml.")

def create_gitignore_entries():
    """Ensure .gitignore includes standard Python ignores."""
    gitignore_path = Path(".gitignore")
    
    required_entries = [
        "# Python",
        "__pycache__/",
        "*.py[cod]",
        "*$py.class",
        ".eggs/",
        "*.egg-info/",
        ".mypy_cache/",
        ".pytest_cache/",
        ".ruff_cache/",
        "build/",
        "dist/",
        "venv/",
        ".venv/",
        "env/",
        ".env",
    ]
    
    if gitignore_path.exists():
        existing = gitignore_path.read_text()
        for entry in required_entries:
            if entry not in existing:
                with open(gitignore_path, "a") as f:
                    f.write(f"\n{entry}\n")
                print(f"Added '{entry}' to .gitignore")
    else:
        with open(gitignore_path, "w") as f:
            f.write("\n".join(required_entries) + "\n")
        print("Created .gitignore with Python entries.")

def main():
    """Main entry point for setup script."""
    print("Configuring linting and formatting tools...")
    
    create_pyproject_config()
    create_gitignore_entries()
    
    print("\nLinting and formatting configuration complete.")
    print("To format code: black code/ tests/")
    print("To lint code: ruff check code/ tests/")

if __name__ == "__main__":
    main()