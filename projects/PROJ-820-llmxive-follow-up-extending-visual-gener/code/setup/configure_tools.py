"""
Configure linting (ruff) and formatting (black) tools.

This script creates the necessary configuration files for ruff and black
to ensure consistent code quality and formatting across the project.
"""
import os
import sys
from pathlib import Path

def create_ruff_config(root_dir: Path) -> None:
    """Create ruff configuration file (pyproject.toml section or .ruff.toml)."""
    ruff_config = """# Ruff configuration for llmXive
    [tool.ruff]
    line-length = 88
    target-version = "py311"
    exclude = [
        ".git",
        "__pycache__",
        ".eggs",
        "build",
        "dist",
        ".tox",
        "venv",
        ".venv",
        "data",
        "figures",
        "state",
    ]

    [tool.ruff.lint]
    select = [
        "E",  # pycodestyle errors
        "W",  # pycodestyle warnings
        "F",  # pyflakes
        "I",  # isort
        "B",  # flake8-bugbear
        "C4", # flake8-comprehensions
        "UP", # pyupgrade
        "N",  # pep8-naming
    ]
    ignore = [
        "E501", # line too long (handled by black)
        "B008", # do not perform function calls in argument defaults
        "C901", # too complex
    ]

    [tool.ruff.lint.per-file-ignores]
    "__init__.py" = ["F401"]
    "tests/*" = ["S101"]

    [tool.ruff.lint.isort]
    known-first-party = ["code", "tests", "specs"]
    """
    
    config_path = root_dir / "pyproject.toml"
    
    # Check if pyproject.toml exists
    if config_path.exists():
        content = config_path.read_text()
        if "[tool.ruff]" in content:
            print("Ruff configuration already exists in pyproject.toml")
            return
        # Append ruff config
        with open(config_path, "a") as f:
            f.write("\n" + ruff_config)
    else:
        # Create new pyproject.toml with ruff config
        with open(config_path, "w") as f:
            f.write(ruff_config)
    
    print(f"Ruff configuration created at {config_path}")

def create_black_config(root_dir: Path) -> None:
    """Create black configuration file."""
    black_config = """[tool.black]
    line-length = 88
    target-version = ['py311']
    include = '\\.pyi?$'
    exclude = '''
    /(
        \\.git
        | __pycache__
        | \\.eggs
        | build
        | dist
        | \\.tox
        | venv
        | \\.venv
        | data
        | figures
        | state
    )/
    '''
    """
    
    # Black config is typically in pyproject.toml
    config_path = root_dir / "pyproject.toml"
    
    if config_path.exists():
        content = config_path.read_text()
        if "[tool.black]" in content:
            print("Black configuration already exists in pyproject.toml")
            return
        # Append black config
        with open(config_path, "a") as f:
            f.write("\n" + black_config)
    else:
        # Create new pyproject.toml with black config
        with open(config_path, "w") as f:
            f.write(black_config)
    
    print(f"Black configuration created at {config_path}")

def create_mypy_config(root_dir: Path) -> None:
    """Create mypy configuration file."""
    mypy_config = """[mypy]
    python_version = 3.11
    warn_return_any = True
    warn_unused_configs = True
    disallow_untyped_defs = True
    check_untyped_defs = True
    ignore_missing_imports = True
    exclude = data|figures|state
    """
    
    config_path = root_dir / "mypy.ini"
    
    if config_path.exists():
        print("Mypy configuration already exists")
        return
    
    with open(config_path, "w") as f:
        f.write(mypy_config)
    
    print(f"Mypy configuration created at {config_path}")

def main() -> int:
    """Main entry point for tool configuration."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    
    print("Configuring linting and formatting tools...")
    
    create_ruff_config(root_dir)
    create_black_config(root_dir)
    create_mypy_config(root_dir)
    
    print("Tool configuration complete.")
    print("\nTo run ruff:")
    print("  ruff check .")
    print("  ruff format .")
    print("\nTo run black:")
    print("  black .")
    print("\nTo run mypy:")
    print("  mypy code/")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
