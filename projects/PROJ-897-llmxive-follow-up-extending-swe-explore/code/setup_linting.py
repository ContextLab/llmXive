import os
import sys
from pathlib import Path
import subprocess

def ensure_requirements() -> None:
    """Ensure linting and formatting tools are installed."""
    tools = ["ruff", "black", "flake8"]
    for tool in tools:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", tool], check=True)
            print(f"Installed: {tool}")
        except subprocess.CalledProcessError:
            print(f"Failed to install: {tool}")

def create_ruff_config() -> None:
    """Create ruff configuration file."""
    base_dir = Path(__file__).resolve().parent.parent
    config_path = base_dir / "pyproject.toml"
    
    content = """[tool.ruff]
line-length = 88
target-version = "py39"

[tool.ruff.lint]
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
    "C901", # too complex
]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]
"tests/*" = ["S101"]
"""
    
    if not config_path.exists():
        config_path.write_text(content)
        print(f"Created: {config_path.relative_to(base_dir)}")
    else:
        print(f"Exists: {config_path.relative_to(base_dir)}")

def create_black_config() -> None:
    """Create black configuration file."""
    base_dir = Path(__file__).resolve().parent.parent
    config_path = base_dir / "pyproject.toml"
    
    # Append to existing if needed, but for simplicity we assume pyproject.toml handles both
    # If separate config needed:
    black_config = base_dir / ".black.toml"
    if not black_config.exists():
        black_config.write_text("[tool.black]\nline-length = 88\ntarget-version = ['py39']\n")
        print(f"Created: {black_config.relative_to(base_dir)}")
    else:
        print(f"Exists: {black_config.relative_to(base_dir)}")

def create_flake8_config() -> None:
    """Create flake8 configuration file."""
    base_dir = Path(__file__).resolve().parent.parent
    config_path = base_dir / ".flake8"
    
    content = """[flake8]
max-line-length = 88
exclude = .git,__pycache__,build,dist,.eggs
ignore = E501,B008,C901
"""
    
    if not config_path.exists():
        config_path.write_text(content)
        print(f"Created: {config_path.relative_to(base_dir)}")
    else:
        print(f"Exists: {config_path.relative_to(base_dir)}")

def main() -> None:
    """Entry point for linting setup."""
    ensure_requirements()
    create_ruff_config()
    create_black_config()
    create_flake8_config()
    print("\nLinting and formatting tools configured.")

if __name__ == "__main__":
    main()