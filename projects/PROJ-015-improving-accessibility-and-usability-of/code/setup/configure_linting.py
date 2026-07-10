"""
Configure linting (ruff) and formatting (black) tools for the project.
"""
import os
import sys
import subprocess
import importlib.metadata
from pathlib import Path

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def ensure_package(package_name: str) -> None:
    """Ensure a package is installed, install it if not."""
    try:
        importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        print(f"Installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

def write_file_if_missing(path: Path, content: str) -> None:
    """Write content to a file only if it doesn't exist."""
    if not path.exists():
        path.write_text(content)
        print(f"Created {path}")
    else:
        print(f"{path} already exists, skipping.")

def main() -> None:
    """Main entry point for configuring linting and formatting."""
    project_root = get_project_root()
    
    # Ensure dependencies are installed
    ensure_package("ruff")
    ensure_package("black")
    
    # Create .ruff.toml configuration
    ruff_config = """[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
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
    write_file_if_missing(project_root / ".ruff.toml", ruff_config)
    
    # Create pyproject.toml with black configuration if it doesn't exist
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        pyproject_content = """[project]
name = "llmXive-project"
version = "0.1.0"
description = "LLM-driven science pipeline project"
requires-python = ">=3.11"

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

[tool.ruff]
# Already configured in .ruff.toml
"""
        pyproject_path.write_text(pyproject_content)
        print(f"Created {pyproject_path}")
    else:
        print(f"{pyproject_path} already exists, skipping.")
    
    print("Linting (ruff) and formatting (black) configuration complete.")

if __name__ == "__main__":
    main()