import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

def run_command(cmd: List[str], check: bool = True) -> Tuple[int, str]:
    """
    Execute a shell command and return the return code and output.
    
    Args:
        cmd: Command and arguments as a list
        check: If True, raise CalledProcessError on non-zero exit
        
    Returns:
        Tuple of (return_code, output)
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=check
        )
        return result.returncode, result.stdout
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout + e.stderr

def check_flake8() -> Tuple[int, str]:
    """
    Run flake8 on the code directory.
    
    Returns:
        Tuple of (return_code, output)
    """
    code_dir = Path(__file__).parent
    cmd = [sys.executable, "-m", "flake8", str(code_dir)]
    return run_command(cmd, check=False)

def check_black(check: bool = True) -> Tuple[int, str]:
    """
    Run black in check mode on the code directory.
    
    Args:
        check: If True, only check formatting (don't fix)
        
    Returns:
        Tuple of (return_code, output)
    """
    code_dir = Path(__file__).parent
    if check:
        cmd = [sys.executable, "-m", "black", "--check", str(code_dir)]
    else:
        cmd = [sys.executable, "-m", "black", str(code_dir)]
    return run_command(cmd, check=False)

def fix_black() -> Tuple[int, str]:
    """
    Run black to fix formatting issues in the code directory.
    
    Returns:
        Tuple of (return_code, output)
    """
    return check_black(check=False)

def setup_config_files() -> None:
    """
    Create configuration files for flake8 and black if they don't exist.
    """
    root = Path(__file__).parent.parent
    
    # Create .flake8 configuration
    flake8_config = root / ".flake8"
    if not flake8_config.exists():
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
        flake8_config.write_text(content)
    
    # Create pyproject.toml with black config if it doesn't exist
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        content = """[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''
"""
        pyproject.write_text(content)

def main() -> int:
    """
    Main entry point for linting configuration and checks.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print("Setting up linting configuration files...")
    setup_config_files()
    
    print("\nRunning flake8...")
    code, output = check_flake8()
    if code == 0:
        print("✓ flake8 passed")
    else:
        print("✗ flake8 failed:")
        print(output)
    
    print("\nRunning black check...")
    code, output = check_black()
    if code == 0:
        print("✓ black check passed")
    else:
        print("✗ black check failed:")
        print(output)
        print("\nTo fix formatting issues, run: python code/config_linting.py --fix")
    
    return code

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--fix":
        print("Fixing formatting with black...")
        code, output = fix_black()
        if code == 0:
            print("✓ Black formatting applied successfully")
        else:
            print("✗ Black failed to fix issues:")
            print(output)
        sys.exit(code)
    else:
        sys.exit(main())