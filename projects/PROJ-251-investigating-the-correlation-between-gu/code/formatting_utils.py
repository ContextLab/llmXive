"""
Formatting utilities for running ruff and black on the codebase.
"""
import subprocess
import sys
import os
from pathlib import Path
from typing import Tuple, Optional

def run_command(command: list, check: bool = True) -> subprocess.CompletedProcess:
    """
    Run a shell command and return the result.
    
    Args:
        command: List of command arguments.
        check: If True, raise CalledProcessError on non-zero exit.
        
    Returns:
        CompletedProcess instance.
    """
    print(f"Running: {' '.join(command)}")
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False
    )
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
        
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, command)
        
    return result

def run_ruff_check_and_fix(code_dir: Path) -> Tuple[bool, str]:
    """
    Run ruff check and fix on the code directory.
    
    Args:
        code_dir: Path to the code directory.
        
    Returns:
        Tuple of (success, message).
    """
    try:
        # Run ruff check first to see what needs fixing
        check_cmd = [sys.executable, "-m", "ruff", "check", str(code_dir)]
        check_result = run_command(check_cmd, check=False)
        
        if check_result.returncode == 0:
            return True, "Ruff check passed with no issues."
        
        # Run ruff fix to automatically fix issues
        fix_cmd = [sys.executable, "-m", "ruff", "check", str(code_dir), "--fix"]
        fix_result = run_command(fix_cmd, check=False)
        
        # Run check again to verify
        final_check = run_command(check_cmd, check=False)
        
        if final_check.returncode == 0:
            return True, "Ruff fix completed successfully. All issues resolved."
        else:
            return False, "Ruff fix completed but some issues remain. Manual intervention may be required."
            
    except Exception as e:
        return False, f"Error running ruff: {str(e)}"

def run_black_format(code_dir: Path) -> Tuple[bool, str]:
    """
    Run black formatting on the code directory.
    
    Args:
        code_dir: Path to the code directory.
        
    Returns:
        Tuple of (success, message).
    """
    try:
        # Run black with --check first to see what needs formatting
        check_cmd = [sys.executable, "-m", "black", "--check", str(code_dir)]
        check_result = run_command(check_cmd, check=False)
        
        if check_result.returncode == 0:
            return True, "Black check passed. Code is already formatted."
        
        # Run black to format the code
        format_cmd = [sys.executable, "-m", "black", str(code_dir)]
        format_result = run_command(format_cmd, check=False)
        
        # Run check again to verify
        final_check = run_command(check_cmd, check=False)
        
        if final_check.returncode == 0:
            return True, "Black formatting completed successfully."
        else:
            return False, "Black formatting completed but some files could not be formatted."
            
    except Exception as e:
        return False, f"Error running black: {str(e)}"

def main():
    """Main entry point for formatting script."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    
    if not code_dir.exists():
        print(f"Error: Code directory not found at {code_dir}")
        sys.exit(1)
        
    print("=" * 60)
    print("Running Ruff Check and Fix")
    print("=" * 60)
    ruff_success, ruff_msg = run_ruff_check_and_fix(code_dir)
    print(f"Ruff Result: {ruff_msg}\n")
    
    print("=" * 60)
    print("Running Black Format")
    print("=" * 60)
    black_success, black_msg = run_black_format(code_dir)
    print(f"Black Result: {black_msg}\n")
    
    if ruff_success and black_success:
        print("All formatting checks passed!")
        sys.exit(0)
    else:
        print("Some formatting issues remain. Please review the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()