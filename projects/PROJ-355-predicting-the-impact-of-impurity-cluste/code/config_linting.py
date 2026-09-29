import os
import subprocess
import sys
from pathlib import Path

from config import get_project_root

def ensure_project_root():
    """Ensure the project root exists and return it."""
    root = get_project_root()
    if not root.exists():
        raise FileNotFoundError(f"Project root not found: {root}")
    return root

def create_ruff_config(root: Path):
    """Create or update pyproject.toml with Ruff configuration."""
    pyproject_path = root / "pyproject.toml"
    
    # Basic Ruff configuration content
    ruff_config = """
[tool.ruff]
line-length = 88
target-version = "py39"
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # Pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
]
exclude = [
    ".git",
    "__pycache__",
    "build",
    "dist",
    ".eggs",
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]

[tool.ruff.isort]
known-first-party = ["code", "tests"]
force-sort-within-sections = true
"""

    # If pyproject.toml exists, we should append or update carefully.
    # For this setup task, we will overwrite if it doesn't have [tool.ruff],
    # but to keep it simple and robust for T003, we create a standalone config
    # or ensure the section exists.
    
    # Strategy: Read existing, check for [tool.ruff], if missing append.
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        if "[tool.ruff]" not in content:
            content = content.rstrip() + "\n\n" + ruff_config
            pyproject_path.write_text(content)
    else:
        # Create minimal pyproject.toml with ruff config if it doesn't exist
        # (Though T001/T001b should have created a basic one, we ensure it here)
        pyproject_path.write_text(ruff_config)

def create_black_config(root: Path):
    """Create or update pyproject.toml with Black configuration."""
    pyproject_path = root / "pyproject.toml"
    
    black_config = """
[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311']
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
"""

    if pyproject_path.exists():
        content = pyproject_path.read_text()
        if "[tool.black]" not in content:
            content = content.rstrip() + "\n\n" + black_config
            pyproject_path.write_text(content)
    else:
        pyproject_path.write_text(black_config)

def verify_tools(root: Path):
    """Verify that ruff and black are installed."""
    tools = ["ruff", "black"]
    missing = []
    
    for tool in tools:
        try:
            subprocess.run(
                [tool, "--version"], 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            print(f"✓ {tool} is installed.")
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append(tool)
            print(f"✗ {tool} is NOT installed.")
    
    if missing:
        print(f"\nMissing tools: {', '.join(missing)}")
        print("Please install them via: pip install ruff black")
        return False
    return True

def main():
    """Main entry point for T003 configuration."""
    root = ensure_project_root()
    print(f"Configuring linting tools for project root: {root}")
    
    create_ruff_config(root)
    create_black_config(root)
    
    if verify_tools(root):
        print("\nLinting configuration successful.")
    else:
        print("\nLinting configuration files created, but tools are missing.")

if __name__ == "__main__":
    main()
