import os
import sys
import subprocess
from pathlib import Path
from config import get_project_root

def ensure_linting_config() -> bool:
    """
    Ensure that linting configuration files exist in the project root.
    Creates default configurations if they are missing.
    """
    root = get_project_root()
    
    # Check for Black configuration (pyproject.toml usually contains this)
    pyproject_path = root / "pyproject.toml"
    ruff_config_path = root / "ruff.toml"
    
    needs_update = False
    
    if not pyproject_path.exists():
        # Create minimal pyproject.toml with Black config
        pyproject_content = """[tool.black]
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
        with open(pyproject_path, 'w') as f:
            f.write(pyproject_content)
        needs_update = True
        
    if not ruff_config_path.exists():
        # Create ruff configuration
        ruff_content = """[tool.ruff]
# Same as Black.
line-length = 88
target-version = "py310"

[tool.ruff.lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
]
ignore = [
    "E501",  # line too long (handled by Black)
    "B008",  # do not perform function calls in argument defaults
    "C901",  # too complex
]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]  # Ignore unused imports in init files
"""
        with open(ruff_config_path, 'w') as f:
            f.write(ruff_content)
        needs_update = True
        
    return needs_update

def run_black_check() -> Tuple[bool, str]:
    """
    Run black --check on the codebase.
    Returns (success, message).
    """
    root = get_project_root()
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", str(root / "code")],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            return True, "Black formatting check passed."
        else:
            return False, f"Black formatting check failed:\n{result.stdout}\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return False, "Black check timed out."
    except Exception as e:
        return False, f"Error running black: {str(e)}"

def run_ruff_check() -> Tuple[bool, str]:
    """
    Run ruff check on the codebase.
    Returns (success, message).
    """
    root = get_project_root()
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(root / "code")],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            return True, "Ruff linting check passed."
        else:
            return False, f"Ruff linting check failed:\n{result.stdout}\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return False, "Ruff check timed out."
    except Exception as e:
        return False, f"Error running ruff: {str(e)}"

def run_black_format() -> Tuple[bool, str]:
    """
    Run black --format on the codebase to fix issues.
    Returns (success, message).
    """
    root = get_project_root()
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", str(root / "code")],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            return True, "Black formatting applied successfully."
        else:
            return False, f"Black formatting failed:\n{result.stdout}\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return False, "Black format timed out."
    except Exception as e:
        return False, f"Error running black format: {str(e)}"

def run_ruff_fix() -> Tuple[bool, str]:
    """
    Run ruff check --fix on the codebase to fix issues.
    Returns (success, message).
    """
    root = get_project_root()
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--fix", str(root / "code")],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0 or result.returncode == 1:
            # ruff returns 1 if fixes were applied but issues remain
            return True, "Ruff fixes applied. Some issues may remain."
        else:
            return False, f"Ruff fix failed:\n{result.stdout}\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return False, "Ruff fix timed out."
    except Exception as e:
        return False, f"Error running ruff fix: {str(e)}"

def main():
    """
    Main entry point for linting tasks.
    1. Ensure config files exist.
    2. Run checks.
    3. If checks fail, attempt to auto-fix.
    4. Re-run checks.
    """
    print("Starting linting and formatting verification...")
    
    # Ensure configs exist
    if ensure_linting_config():
        print("Created default linting configuration files.")
    
    # Run checks
    black_ok, black_msg = run_black_check()
    ruff_ok, ruff_msg = run_ruff_check()
    
    print(f"Black: {black_msg}")
    print(f"Ruff: {ruff_msg}")
    
    if black_ok and ruff_ok:
        print("All checks passed!")
        return 0
    
    print("Issues found. Attempting to auto-fix...")
    
    # Attempt fixes
    if not black_ok:
        success, msg = run_black_format()
        print(f"Black fix: {msg}")
    
    if not ruff_ok:
        success, msg = run_ruff_fix()
        print(f"Ruff fix: {msg}")
    
    # Re-run checks
    print("\nRe-running checks after fixes...")
    black_ok, black_msg = run_black_check()
    ruff_ok, ruff_msg = run_ruff_check()
    
    print(f"Black: {black_msg}")
    print(f"Ruff: {ruff_msg}")
    
    if black_ok and ruff_ok:
        print("All issues resolved!")
        return 0
    else:
        print("Some issues remain. Manual intervention required.")
        return 1

if __name__ == "__main__":
    sys.exit(main())