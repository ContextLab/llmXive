"""
Setup script for linting (ruff) and formatting (black) tools.
This script creates configuration files and provides verification utilities.
"""
import subprocess
import sys
from pathlib import Path
import os
import tomli_w
import tomli
import json


def check_tool(tool_name: str) -> bool:
    """Check if a tool is installed."""
    try:
        subprocess.run([tool_name, "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_tools() -> None:
    """Install ruff and black if not present."""
    tools = ["ruff", "black"]
    for tool in tools:
        if not check_tool(tool):
            print(f"Installing {tool}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", tool])
        else:
            print(f"{tool} is already installed.")


def create_ruff_config(project_root: Path) -> None:
    """Create a ruff.toml configuration file."""
    config_content = {
        "target-version": "py311",
        "line-length": 88,
        "select": [
            "E",  # pycodestyle errors
            "W",  # pycodestyle warnings
            "F",  # Pyflakes
            "I",  # isort
            "B",  # flake8-bugbear
            "C4", # flake8-comprehensions
            "UP", # pyupgrade
        ],
        "ignore": [
            "E501",  # line too long (handled by black)
            "B008",  # do not perform function calls in argument defaults
        ],
        "exclude": [
            ".git",
            "__pycache__",
            ".venv",
            "venv",
            "build",
            "dist",
        ],
        "per-file-ignores": {
            "__init__.py": ["F401"],  # Allow unused imports in __init__.py
        },
    }

    config_path = project_root / "ruff.toml"
    # Write as TOML manually to avoid dependency on tomli_w if not installed
    # But since we are in a setup script, let's try to use a simple approach
    # or just write the content as a string if tomli_w is not available.
    
    # Fallback to string writing for portability
    lines = [
        f'target-version = "{config_content["target-version"]}"',
        f'line-length = {config_content["line-length"]}',
        f'select = {config_content["select"]}',
        f'ignore = {config_content["ignore"]}',
        f'exclude = {config_content["exclude"]}',
    ]
    
    # Handle per-file-ignores
    lines.append("per-file-ignores = {")
    for k, v in config_content["per-file-ignores"].items():
        lines.append(f'  "{k}" = {v}')
    lines.append("}")

    config_path.write_text("\n".join(lines))
    print(f"Created {config_path}")


def create_black_config(project_root: Path) -> None:
    """Create a pyproject.toml configuration section for black."""
    pyproject_path = project_root / "pyproject.toml"
    
    # Read existing content if present
    content = ""
    if pyproject_path.exists():
        content = pyproject_path.read_text()
    
    # Define the black section
    black_section = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | venv
  | _build
  | buck-out
  | build
  | dist
)/
'''
"""
    
    # Check if [tool.black] already exists
    if "[tool.black]" not in content:
        with open(pyproject_path, "a") as f:
            f.write(black_section)
        print(f"Added black configuration to {pyproject_path}")
    else:
        print(f"Black configuration already exists in {pyproject_path}")


def verify_setup(project_root: Path) -> bool:
    """Verify that ruff and black are installed and configured."""
    print("Verifying setup...")
    
    # Check tools
    ruff_ok = check_tool("ruff")
    black_ok = check_tool("black")
    
    if not ruff_ok:
        print("ERROR: ruff is not installed.")
        return False
    if not black_ok:
        print("ERROR: black is not installed.")
        return False
    
    # Check config files
    ruff_config = project_root / "ruff.toml"
    pyproject = project_root / "pyproject.toml"
    
    if not ruff_config.exists():
        print("ERROR: ruff.toml not found.")
        return False
    
    if not pyproject.exists() or "[tool.black]" not in pyproject.read_text():
        print("ERROR: pyproject.toml missing [tool.black] section.")
        return False
    
    print("Setup verified successfully.")
    return True


def main() -> int:
    """Main entry point."""
    project_root = Path(__file__).resolve().parent.parent
    
    print("Setting up linting and formatting tools...")
    
    # Install tools
    install_tools()
    
    # Create configs
    create_ruff_config(project_root)
    create_black_config(project_root)
    
    # Verify
    if verify_setup(project_root):
        print("Linting and formatting setup complete.")
        return 0
    else:
        print("Setup verification failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())