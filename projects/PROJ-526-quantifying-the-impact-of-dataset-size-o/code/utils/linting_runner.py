"""
Utility to run linting and formatting checks programmatically.
Used by CI/CD or local validation scripts to enforce code quality.
"""
import subprocess
import sys
from pathlib import Path
from typing import Tuple, Optional

from code.linting_config import get_black_config, get_flake8_config

def run_black_check(target_dir: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Runs Black formatter in 'check' mode on the target directory.
    
    Args:
        target_dir: Directory to check. Defaults to project root.
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    if target_dir is None:
        target_dir = Path(__file__).resolve().parent.parent.parent
        
    config = get_black_config()
    cmd = [
        sys.executable, "-m", "black",
        "--check",
        f"--line-length={config['line_length']}",
        "--diff"
    ]
    
    # Add exclude patterns if needed, though pyproject.toml is preferred
    try:
        result = subprocess.run(
            cmd + [str(target_dir)],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            return True, "Black check passed."
        else:
            msg = f"Black check failed:\n{result.stdout}\n{result.stderr}"
            return False, msg
    except FileNotFoundError:
        return False, "Black not installed. Run: pip install black"

def run_flake8_check(target_dir: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Runs Flake8 linter on the target directory.
    
    Args:
        target_dir: Directory to check. Defaults to project root.
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    if target_dir is None:
        target_dir = Path(__file__).resolve().parent.parent.parent
        
    config = get_flake8_config()
    ignore_str = ",".join(config["ignore"])
    
    cmd = [
        sys.executable, "-m", "flake8",
        f"--max-line-length={config['max_line_length']}",
        f"--ignore={ignore_str}",
        "--exclude", ",".join(config["exclude"]),
        str(target_dir)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            return True, "Flake8 check passed."
        else:
            msg = f"Flake8 check failed:\n{result.stdout}\n{result.stderr}"
            return False, msg
    except FileNotFoundError:
        return False, "Flake8 not installed. Run: pip install flake8"

def main() -> int:
    """
    Main entry point for running all linting checks.
    Returns 0 if all pass, 1 otherwise.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    all_passed = True
    
    print("Running Black check...")
    success, msg = run_black_check(project_root)
    if not success:
        print(f"❌ {msg}")
        all_passed = False
    else:
        print(f"✅ {msg}")
        
    print("\nRunning Flake8 check...")
    success, msg = run_flake8_check(project_root)
    if not success:
        print(f"❌ {msg}")
        all_passed = False
    else:
        print(f"✅ {msg}")
        
    if all_passed:
        print("\n🎉 All linting checks passed!")
        return 0
    else:
        print("\n⚠️ Some linting checks failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
