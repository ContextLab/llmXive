"""
Setup script for linting (ruff) and formatting (black) tools.
Generates configuration files: pyproject.toml and ruff.toml.
"""
import os
import subprocess
import sys
from pathlib import Path

def ensure_project_root():
    """Ensure we are running from the project root."""
    project_root = Path(__file__).resolve().parent.parent
    if not (project_root / "code").exists():
        print(f"Error: 'code' directory not found at {project_root}")
        sys.exit(1)
    return project_root

def write_pyproject_toml(project_root: Path):
    """Write Black configuration to pyproject.toml."""
    config_content = """[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \\.git
  | \\.mypy_cache
  | \\.venv
  | venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
line_length = 88
"""
    file_path = project_root / "pyproject.toml"
    if file_path.exists():
        print(f"Warning: {file_path} already exists. Skipping overwrite.")
    else:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(config_content)
        print(f"Created {file_path}")

def write_ruff_toml(project_root: Path):
    """Write Ruff configuration to ruff.toml."""
    config_content = """[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
]
ignore = [
    "E501",  # line too long (handled by black)
    "B008",  # do not perform function calls in argument defaults
    "C901",  # too complex
]

[lint.per-file-ignores]
"__init__.py" = ["F401"]  # Allow unused imports in init files

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    file_path = project_root / "ruff.toml"
    if file_path.exists():
        print(f"Warning: {file_path} already exists. Skipping overwrite.")
    else:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(config_content)
        print(f"Created {file_path}")

def main():
    """Main entry point for linting setup."""
    print("Setting up linting and formatting tools...")
    project_root = ensure_project_root()

    write_pyproject_toml(project_root)
    write_ruff_toml(project_root)

    # Check if tools are installed
    print("\nChecking tool availability...")
    tools = ["black", "ruff"]
    for tool in tools:
        try:
            subprocess.run(
                [sys.executable, "-m", tool, "--version"],
                check=True,
                capture_output=True,
            )
            print(f"  ✓ {tool} is installed")
        except subprocess.CalledProcessError:
            print(f"  ✗ {tool} is NOT installed. Run: pip install {tool}")
            # Do not exit, just warn. The user can install manually or via requirements.txt.

    print("\nLinting and formatting configuration complete.")

if __name__ == "__main__":
    main()