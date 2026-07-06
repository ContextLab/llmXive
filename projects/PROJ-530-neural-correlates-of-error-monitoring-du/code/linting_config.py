import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FLAKE8_CONFIG_FILE = PROJECT_ROOT / ".flake8"
BLACK_CONFIG_FILE = PROJECT_ROOT / "pyproject.toml"

def get_flake8_command():
    """Returns the flake8 command with project-specific configuration."""
    return [
        sys.executable, "-m", "flake8",
        "--config", str(FLAKE8_CONFIG_FILE),
        str(PROJECT_ROOT / "code"),
        str(PROJECT_ROOT / "tests")
    ]

def get_black_command():
    """Returns the black command with project-specific configuration."""
    return [
        sys.executable, "-m", "black",
        "--config", str(BLACK_CONFIG_FILE),
        "--check",
        str(PROJECT_ROOT / "code"),
        str(PROJECT_ROOT / "tests")
    ]

def run_linter():
    """Runs flake8 and returns the exit code."""
    cmd = get_flake8_command()
    print(f"Running linter: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode

def run_formatter():
    """Runs black (check mode) and returns the exit code."""
    cmd = get_black_command()
    print(f"Running formatter: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode

def create_config_files():
    """Creates the .flake8 and pyproject.toml configuration files if they don't exist."""
    flake8_content = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    build,
    dist,
    *.egg-info
"""
    
    black_content = """[tool.black]
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

    if not FLAKE8_CONFIG_FILE.exists():
        with open(FLAKE8_CONFIG_FILE, "w") as f:
            f.write(flake8_content)
        print(f"Created {FLAKE8_CONFIG_FILE}")
    
    # We need to check if pyproject.toml exists and append the tool.black section if not
    # For simplicity in this task, we assume we are creating the section or the file if empty
    # A robust implementation would parse existing toml, but for config setup:
    if not BLACK_CONFIG_FILE.exists():
        with open(BLACK_CONFIG_FILE, "w") as f:
            f.write(black_content)
        print(f"Created {BLACK_CONFIG_FILE}")
    else:
        # Check if [tool.black] already exists
        with open(BLACK_CONFIG_FILE, "r") as f:
            content = f.read()
        if "[tool.black]" not in content:
            with open(BLACK_CONFIG_FILE, "a") as f:
                f.write("\n" + black_content)
            print(f"Appended [tool.black] to {BLACK_CONFIG_FILE}")
        else:
            print(f"{BLACK_CONFIG_FILE} already contains [tool.black]")