import os
import subprocess
import sys
from pathlib import Path

def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

def write_config_file(path: Path, content: str) -> None:
    """Write configuration content to a file."""
    ensure_directory(path.parent)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def setup_ruff_config(root: Path) -> None:
    """Create or update ruff configuration."""
    # We rely on pyproject.toml for ruff config, but we ensure the file exists
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        # Fallback: create minimal pyproject if missing
        content = """
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[tool.ruff]
line-length = 88
target-version = "py39"
select = ["E", "W", "F", "I", "C", "B"]
ignore = ["E501", "B008", "C901"]
"""
        write_config_file(pyproject, content)

def setup_black_config(root: Path) -> None:
    """Create or update black configuration."""
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        content = """
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[tool.black]
line-length = 88
target-version = ['py39']
"""
        write_config_file(pyproject, content)
    else:
        # Check if [tool.black] section exists; if not, append it
        with open(pyproject, 'r', encoding='utf-8') as f:
            content = f.read()
        if "[tool.black]" not in content:
            black_section = """

[tool.black]
line-length = 88
target-version = ['py39']
include = '\\\\.pyi?$'
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
            with open(pyproject, 'a', encoding='utf-8') as f:
                f.write(black_section)

def install_tools() -> None:
    """Install ruff and black if not already installed."""
    print("Ensuring linting and formatting tools are installed...")
    try:
        import ruff
        print("  ruff is already installed.")
    except ImportError:
        print("  Installing ruff...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ruff"])

    try:
        import black
        print("  black is already installed.")
    except ImportError:
        print("  Installing black...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "black"])

def main() -> None:
    """Main entry point for setting up linting and formatting."""
    root = Path(__file__).parent
    print(f"Configuring linting (ruff) and formatting (black) in: {root}")

    install_tools()
    setup_ruff_config(root)
    setup_black_config(root)

    print("Linting and formatting configuration complete.")
    print("You can now run:")
    print("  ruff check .        # Lint code")
    print("  black .             # Format code")
    print("  ruff check . --fix  # Auto-fix linting issues")

if __name__ == "__main__":
    main()