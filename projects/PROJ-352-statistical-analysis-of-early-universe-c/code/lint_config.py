"""
Linting and formatting configuration utilities for the CMB analysis pipeline.

This module provides functions to check code quality using flake8, pylint, and black.
It also provides setup functions to initialize configuration files if they don't exist.
"""
import subprocess
import sys
from pathlib import Path
import os

def setup_black():
    """Initialize Black configuration in pyproject.toml if not present."""
    root = Path(__file__).parent.parent
    pyproject = root / "pyproject.toml"
    
    if not pyproject.exists():
        content = """[tool.black]
line-length = 88
target-version = ['py38']
include = 'code/.*\\.pyi?$'
exclude = '''
(
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
)
'''
"""
        pyproject.write_text(content)
        print("Created pyproject.toml with Black configuration.")
    else:
        # Check if [tool.black] section exists
        content = pyproject.read_text()
        if "[tool.black]" not in content:
            # Append Black config
            content += "\n[tool.black]\nline-length = 88\ntarget-version = ['py38']\n"
            pyproject.write_text(content)
            print("Added Black configuration to pyproject.toml.")
        else:
            print("Black configuration already present in pyproject.toml.")

def setup_flake8():
    """Initialize flake8 configuration in setup.cfg if not present."""
    root = Path(__file__).parent.parent
    setup_cfg = root / "setup.cfg"
    
    if not setup_cfg.exists():
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
"""
        setup_cfg.write_text(content)
        print("Created setup.cfg with flake8 configuration.")
    else:
        content = setup_cfg.read_text()
        if "[flake8]" not in content:
            content += "\n[flake8]\nmax-line-length = 88\nextend-ignore = E203, W503\n"
            setup_cfg.write_text(content)
            print("Added flake8 configuration to setup.cfg.")
        else:
            print("flake8 configuration already present in setup.cfg.")

def setup_pylint():
    """Initialize pylint configuration in .pylintrc if not present."""
    root = Path(__file__).parent.parent
    pylintrc = root / ".pylintrc"
    
    if not pylintrc.exists():
        content = """[MASTER]
ignore=CVS

[MESSAGES CONTROL]
disable=C0103,C0114,C0115,C0116,R0903,R0904,R0913,R0914,W0511

[FORMAT]
max-line-length=88

[DESIGN]
max-args=10
max-locals=15
max-returns=6
max-branches=12
max-statements=50
max-attributes=10
max-public-methods=20
"""
        pylintrc.write_text(content)
        print("Created .pylintrc with pylint configuration.")
    else:
        print(".pylintrc already exists.")

def check_black():
    """Run Black formatter on the code directory."""
    root = Path(__file__).parent.parent
    code_dir = root / "code"
    
    if not code_dir.exists():
        print("code/ directory not found.")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "--diff", str(code_dir)],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            print("Black formatting check passed.")
            return True
        else:
            print("Black formatting issues found:")
            print(result.stdout)
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("Black not installed. Install with: pip install black")
        return False
    except subprocess.TimeoutExpired:
        print("Black check timed out.")
        return False

def check_flake8():
    """Run flake8 linter on the code directory."""
    root = Path(__file__).parent.parent
    code_dir = root / "code"
    
    if not code_dir.exists():
        print("code/ directory not found.")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", str(code_dir)],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            print("flake8 check passed.")
            return True
        else:
            print("flake8 issues found:")
            print(result.stdout)
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("flake8 not installed. Install with: pip install flake8")
        return False
    except subprocess.TimeoutExpired:
        print("flake8 check timed out.")
        return False

def check_pylint():
    """Run pylint on the code directory."""
    root = Path(__file__).parent.parent
    code_dir = root / "code"
    
    if not code_dir.exists():
        print("code/ directory not found.")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pylint", str(code_dir), "--rcfile=.pylintrc"],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0 or result.returncode == 1:
            # Return code 1 means issues found but not fatal
            if "Your code has been rated at" in result.stdout:
                print("pylint check completed.")
                print(result.stdout)
                return True
            else:
                print("pylint issues found:")
                print(result.stdout)
                print(result.stderr)
                return False
        else:
            print("pylint check failed:")
            print(result.stdout)
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("pylint not installed. Install with: pip install pylint")
        return False
    except subprocess.TimeoutExpired:
        print("pylint check timed out.")
        return False

def main():
    """Run all linting and formatting checks."""
    root = Path(__file__).parent.parent
    
    # Ensure configuration files exist
    setup_black()
    setup_flake8()
    setup_pylint()
    
    print("\n--- Running Black Check ---")
    black_ok = check_black()
    
    print("\n--- Running flake8 Check ---")
    flake8_ok = check_flake8()
    
    print("\n--- Running pylint Check ---")
    pylint_ok = check_pylint()
    
    print("\n--- Summary ---")
    if black_ok and flake8_ok and pylint_ok:
        print("All linting and formatting checks passed.")
        return 0
    else:
        print("Some checks failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())