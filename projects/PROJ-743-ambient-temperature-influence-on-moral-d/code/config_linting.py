import os
import sys
from pathlib import Path
from config import get_path_env_override

def ensure_pyproject_toml():
    """Create or update pyproject.toml with black and ruff configuration."""
    root = Path(get_path_env_override())
    pyproject_path = root / "pyproject.toml"
    
    config_content = """[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311']
include = '\\.pyi?$'
extend-exclude = '''
/(
  # directories
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

[tool.ruff]
line-length = 88
target-version = "py39"
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
    "C901", # too complex
]
exclude = [
    ".eggs",
    ".git",
    ".mypy_cache",
    ".tox",
    ".venv",
    "_build",
    "buck-out",
    "build",
    "dist",
]

[tool.ruff.isort]
known-first-party = ["config", "utils", "loaders", "ingestion", "modeling"]
"""
    
    if not pyproject_path.exists():
        pyproject_path.write_text(config_content)
        print(f"Created {pyproject_path}")
    else:
        print(f"pyproject.toml already exists at {pyproject_path}")

def ensure_ruff_config():
    """Ensure ruff configuration is present (can be in pyproject.toml or .ruff.toml)."""
    root = Path(get_path_env_override())
    ruff_toml = root / ".ruff.toml"
    pyproject_path = root / "pyproject.toml"
    
    # Check if ruff config already exists in pyproject.toml
    if pyproject_path.exists() and "[tool.ruff]" in pyproject_path.read_text():
        print("Ruff configuration already exists in pyproject.toml")
        return
    
    # Create standalone .ruff.toml if not in pyproject.toml
    config_content = """[lint]
select = ["E", "W", "F", "I", "B", "C4"]
ignore = ["E501", "B008", "C901"]
exclude = [
    ".eggs",
    ".git",
    ".mypy_cache",
    ".tox",
    ".venv",
    "_build",
    "buck-out",
    "build",
    "dist",
]

[lint.isort]
known-first-party = ["config", "utils", "loaders", "ingestion", "modeling"]
"""
    
    if not ruff_toml.exists():
        ruff_toml.write_text(config_content)
        print(f"Created {ruff_toml}")
    else:
        print(f".ruff.toml already exists at {ruff_toml}")

def ensure_flake8_config():
    """Create or update .flake8 configuration file."""
    root = Path(get_path_env_override())
    flake8_path = root / ".flake8"
    
    config_content = """[flake8]
max-line-length = 88
exclude = 
    .eggs,
    .git,
    .mypy_cache,
    .tox,
    .venv,
    _build,
    buck-out,
    build,
    dist,
ignore = E501, B008, C901
"""
    
    if not flake8_path.exists():
        flake8_path.write_text(config_content)
        print(f"Created {flake8_path}")
    else:
        print(f".flake8 already exists at {flake8_path}")

def main():
    """Main entry point for linting configuration setup."""
    print("Setting up linting and formatting configuration...")
    
    ensure_pyproject_toml()
    ensure_ruff_config()
    ensure_flake8_config()
    
    print("\nLinting and formatting configuration complete.")
    print("You can now run:")
    print("  - black code/ tests/  # to format code")
    print("  - ruff check code/ tests/  # to lint code")
    print("  - flake8 code/ tests/  # to lint with flake8")

if __name__ == "__main__":
    main()