"""
Script to configure and install linting (ruff) and formatting (black) tools.
This script ensures the necessary configuration files are present and
installs the tools into the environment.
"""
import os
import subprocess
import sys
from pathlib import Path

def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")

def write_config_file(path: Path, content: str) -> None:
    """Write content to a file, creating parent directories if needed."""
    ensure_directory(path.parent)
    if not path.exists():
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Created config file: {path}")
    else:
        print(f"Config file already exists: {path} (skipping)")

def setup_ruff_config(project_root: Path) -> None:
    """Create or update ruff configuration in pyproject.toml."""
    # We assume ruff settings are in pyproject.toml as per modern best practices.
    # This function acts as a verifier or initializer if pyproject.toml is missing.
    pyproject_path = project_root / "pyproject.toml"
    
    if not pyproject_path.exists():
        # Fallback: create a minimal pyproject.toml with ruff config if missing entirely
        config = """[tool.ruff]
line-length = 88
target-version = "py39"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "C", "B"]
ignore = ["E501", "B008"]
"""
        write_config_file(pyproject_path, config)
    else:
        print(f"Found existing pyproject.toml at {pyproject_path}. Ensure [tool.ruff] section is configured.")

def setup_black_config(project_root: Path) -> None:
    """Create or update black configuration in pyproject.toml."""
    pyproject_path = project_root / "pyproject.toml"
    
    if not pyproject_path.exists():
        # Fallback: create minimal pyproject.toml with black config
        config = """[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311']
"""
        write_config_file(pyproject_path, config)
    else:
        print(f"Found existing pyproject.toml at {pyproject_path}. Ensure [tool.black] section is configured.")

def install_tools() -> None:
    """Install ruff and black using pip."""
    print("Installing linting and formatting tools...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ruff", "black"])
        print("Successfully installed ruff and black.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install tools: {e}", file=sys.stderr)
        sys.exit(1)

def main() -> None:
    """Main entry point for setup_linting."""
    # Determine project root (assuming script is in code/)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent if script_dir.name == "code" else script_dir

    print(f"Project root detected at: {project_root}")

    # 1. Install tools
    install_tools()

    # 2. Ensure configuration files exist
    setup_ruff_config(project_root)
    setup_black_config(project_root)

    print("Linting and formatting configuration complete.")
    print("To run linter: ruff check .")
    print("To run formatter: black .")

if __name__ == "__main__":
    main()
