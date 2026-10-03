"""
Setup Linting and Formatting Configuration for llmXive Project.

This module creates the necessary configuration files for Ruff (linting)
and Black (formatting) to ensure consistent code style across the project.
"""
import os
import sys
import subprocess
from pathlib import Path


def ensure_project_root() -> Path:
    """Ensure we are running from the project root."""
    current = Path.cwd()
    # Look for the specific project directory
    project_root = current / "projects" / "PROJ-915-llmxive-follow-up-extending-measuring-ep"
    
    if not project_root.exists():
        # If not in the specific project dir, check if we are in it directly
        if (current / "code").exists() and (current / "data").exists():
            project_root = current
        else:
            # Fallback: assume current directory is the root
            project_root = current
            
    return project_root


def write_pyproject_toml(root: Path) -> None:
    """Create or update pyproject.toml with Black configuration."""
    pyproject_path = root / "pyproject.toml"
    
    config_content = """[tool.black]
line-length = 88
target-version = ['py311']
include = 'code/.*\\.py'
extend-exclude = '''
/(
  # directories
  \\(venv|build|dist|\\.eggs\\)
)/
'''

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
"""
    
    if pyproject_path.exists():
        # Read existing content and append/merge if necessary
        existing = pyproject_path.read_text()
        if "[tool.black]" not in existing:
            pyproject_path.write_text(existing + "\n" + config_content)
        else:
            # Update existing black config if needed (simplified: just ensure it's there)
            pass
    else:
        pyproject_path.write_text(config_content)


def write_ruff_toml(root: Path) -> None:
    """Create .ruff.toml with linting rules."""
    ruff_path = root / ".ruff.toml"
    
    config_content = """# Ruff configuration for llmXive
target-version = "py311"
line-length = 88

[lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # Pyflakes
    "I",   # isort
    "C",   # flake8-comprehensions
    "B",   # flake8-bugbear
    "UP",  # pyupgrade
    "RUF", # Ruff-specific rules
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
    "C901", # too complex
]

[lint.per-file-ignores]
"tests/*" = ["S101"] # allow assert in tests

[lint.isort]
known-first-party = ["code", "agents"]
"""
    
    ruff_path.write_text(config_content)


def install_tools(root: Path) -> None:
    """Install linting and formatting tools if not present."""
    tools = ["ruff", "black"]
    
    for tool in tools:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", tool], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print(f"Warning: Failed to install {tool}. Please install manually.")


def main() -> None:
    """Main entry point for setting up linting and formatting."""
    root = ensure_project_root()
    print(f"Setting up linting and formatting in: {root}")
    
    # Install tools
    install_tools(root)
    
    # Write configuration files
    write_pyproject_toml(root)
    write_ruff_toml(root)
    
    print("Linting (Ruff) and Formatting (Black) configuration created successfully.")
    print(f"  - {root / 'pyproject.toml'}")
    print(f"  - {root / '.ruff.toml'}")
    print("\nTo run linting:   ruff check code/")
    print("To run formatting: black code/")


if __name__ == "__main__":
    main()