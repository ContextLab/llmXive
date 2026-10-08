import os
import sys
from pathlib import Path

def create_ruff_config(path: Path) -> None:
    """Create ruff.toml configuration file."""
    config_content = """# Ruff configuration for llmXive pipeline
line-length = 88
target-version = "py311"

[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
]

[lint.isort]
known-first-party = ["simulation", "generation", "evaluation", "analysis", "utils", "setup"]
force-single-line = true
"""
    with open(path / "ruff.toml", 'w') as f:
        f.write(config_content)
    print(f"Created ruff.toml at {path / 'ruff.toml'}")

def create_black_config(path: Path) -> None:
    """Create pyproject.toml with Black configuration."""
    config_content = """[tool.black]
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
"""
    pyproject_path = path / "pyproject.toml"
    if pyproject_path.exists():
        with open(pyproject_path, 'r') as f:
            content = f.read()
        if "[tool.black]" not in content:
            with open(pyproject_path, 'a') as f:
                f.write("\n" + config_content)
        print(f"Added Black configuration to pyproject.toml")
    else:
        with open(pyproject_path, 'w') as f:
            f.write(config_content)
        print(f"Created pyproject.toml with Black configuration at {pyproject_path}")

def create_mypy_config(path: Path) -> None:
    """Create mypy.ini configuration file."""
    config_content = """[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
ignore_missing_imports = True
"""
    with open(path / "mypy.ini", 'w') as f:
        f.write(config_content)
    print(f"Created mypy.ini at {path / 'mypy.ini'}")

def main() -> None:
    """Main function for configure_tools module."""
    root = Path(__file__).resolve().parent.parent.parent
    create_ruff_config(root)
    create_black_config(root)
    create_mypy_config(root)
    print("All tool configurations have been created.")

if __name__ == "__main__":
    main()
