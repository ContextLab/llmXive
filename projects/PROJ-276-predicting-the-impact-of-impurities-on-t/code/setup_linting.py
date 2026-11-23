"""
Setup script to initialize linting and formatting tools (Ruff and Black).
This script ensures configuration files exist and tools are installed.
"""
import os
import subprocess
import sys
from pathlib import Path

def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)

def write_config_file(path: Path, content: str) -> None:
    """Write content to a configuration file."""
    path.write_text(content, encoding="utf-8")
    print(f"Created: {path}")

def setup_ruff_config(root: Path) -> None:
    """Create ruff.toml configuration file."""
    config_path = root / "ruff.toml"
    if config_path.exists():
        print(f"ruff.toml already exists at {config_path}, skipping.")
        return

    config_content = """# Ruff configuration for llmXive project
line-length = 88
target-version = "py39"

[lint]
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
    "E501", # Line too long (handled by Black)
    "B008", # Do not perform function call in argument defaults
]

exclude = [
    ".git",
    ".tox",
    "__pycache__",
    "build",
    "dist",
    "data/",
    "state/",
    "docs/",
]

[lint.isort]
known-first-party = ["code"]
force-sort-within-sections = true
combine-as-imports = true
"""
    write_config_file(config_path, config_content)

def setup_black_config(root: Path) -> None:
    """Create pyproject.toml with Black configuration if not present."""
    config_path = root / "pyproject.toml"
    if config_path.exists():
        content = config_path.read_text(encoding="utf-8")
        if "[tool.black]" in content:
            print(f"Black config already exists in {config_path}, skipping.")
            return

    # Read existing content or start fresh
    base_content = ""
    if config_path.exists():
        base_content = config_path.read_text(encoding="utf-8")

    black_section = """
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
    write_config_file(config_path, base_content + black_section)

def install_tools() -> None:
    """Install ruff and black if not already installed."""
    print("Checking for ruff...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "ruff"])
        print("ruff installed successfully.")
    except subprocess.CalledProcessError:
        print("Failed to install ruff. Please install manually: pip install ruff")

    print("Checking for black...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "black"])
        print("black installed successfully.")
    except subprocess.CalledProcessError:
        print("Failed to install black. Please install manually: pip install black")

def main() -> None:
    """Main entry point for setup_linting."""
    root = Path(__file__).parent
    print(f"Setting up linting tools in {root}...")

    setup_ruff_config(root)
    setup_black_config(root)
    install_tools()

    print("Linting setup complete. Run 'ruff check .' and 'black .' to validate.")

if __name__ == "__main__":
    main()