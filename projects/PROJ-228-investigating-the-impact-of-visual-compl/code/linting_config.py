"""
Configuration and setup for linting (flake8) and formatting (black) tools.
This module provides a script to initialize the project's linting environment
and generate configuration files if they do not exist.
"""
import os
import subprocess
import sys
from pathlib import Path

def ensure_config_files():
    """Create .flake8 and pyproject.toml (for black) if they don't exist."""
    root = Path(__file__).parent.parent
    
    # .flake8 configuration
    flake8_path = root / ".flake8"
    if not flake8_path.exists():
        content = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    build,
    dist,
    .eggs,
    *.egg-info
max-complexity = 10
"""
        flake8_path.write_text(content)
        print(f"Created {flake8_path}")
    else:
        print(f"Found existing {flake8_path}")

    # pyproject.toml for Black
    pyproject_path = root / "pyproject.toml"
    if not pyproject_path.exists():
        content = """[tool.black]
line-length = 88
target-version = ['py310']
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
        pyproject_path.write_text(content)
        print(f"Created {pyproject_path}")
    else:
        print(f"Found existing {pyproject_path}")

def install_tools():
    """Install black and flake8 if not present."""
    tools = ["black", "flake8"]
    for tool in tools:
        try:
            __import__(tool.replace("-", "_"))
            print(f"{tool} is already installed.")
        except ImportError:
            print(f"Installing {tool}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", tool])

def run_black(paths=None):
    """Run black on the specified paths or default to code/ and tests/."""
    if paths is None:
        paths = ["code", "tests"]
    
    cmd = ["black"] + paths
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("Black formatting failed or had issues.")
        return False
    print("Black formatting successful.")
    return True

def run_flake8(paths=None):
    """Run flake8 on the specified paths or default to code/ and tests/."""
    if paths is None:
        paths = ["code", "tests"]
    
    cmd = ["flake8"] + paths
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("Flake8 found issues.")
        return False
    print("Flake8 passed.")
    return True

def main():
    """Main entry point for configuring and running linting/formatting."""
    ensure_config_files()
    install_tools()
    
    print("\n--- Running Black ---")
    run_black()
    
    print("\n--- Running Flake8 ---")
    run_flake8()

if __name__ == "__main__":
    main()