import subprocess
import sys
from pathlib import Path
import os

def install_tools():
    """Install ruff and black if not present."""
    print("Installing linting and formatting tools...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ruff", "black", "--quiet"])
        print("Tools installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install tools: {e}")
        sys.exit(1)

def create_ruff_config(project_root: Path):
    """Create a .ruff.toml configuration file."""
    config_content = """[lint]
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
]

[lint.per-file-ignores]
"__init__.py" = ["F401"]

[format]
# Same as Black.
line-length = 88
indent-style = "space"
"""
    config_path = project_root / ".ruff.toml"
    with open(config_path, "w") as f:
        f.write(config_content)
    print(f"Created ruff config at {config_path}")

def create_black_config(project_root: Path):
    """Create a pyproject.toml configuration for Black if not exists, or update it."""
    pyproject_path = project_root / "pyproject.toml"
    
    black_section = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
"""
    
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        if "[tool.black]" not in content:
            with open(pyproject_path, "a") as f:
                f.write(black_section)
            print(f"Updated pyproject.toml with Black config at {pyproject_path}")
        else:
            print("Black config already exists in pyproject.toml")
    else:
        with open(pyproject_path, "w") as f:
            f.write(black_section)
        print(f"Created pyproject.toml with Black config at {pyproject_path}")

def main():
    """Main entry point for linting setup."""
    # Determine project root (assume script is in code/ directory)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    print(f"Setting up linting in project root: {project_root}")
    
    install_tools()
    create_ruff_config(project_root)
    create_black_config(project_root)
    
    print("Linting and formatting configuration complete.")
    print("You can now run: ruff check . && black .")

if __name__ == "__main__":
    main()