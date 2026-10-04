"""
Script to run ruff static analysis on the codebase and fix issues.

This script executes 'ruff check' on the code/ directory. If issues are found,
it attempts to auto-fix them using 'ruff check --fix'. It reports the final
status and writes a summary to the results directory.
"""
import subprocess
import sys
import os
from pathlib import Path
import json
from datetime import datetime

def run_ruff_check(code_dir: Path, fix: bool = False) -> tuple[int, str, str]:
    """
    Run ruff check on the specified directory.
    
    Args:
        code_dir: Path to the code directory to check
        fix: If True, attempt to auto-fix issues
        
    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    cmd = [sys.executable, "-m", "ruff", "check", str(code_dir)]
    if fix:
        cmd.append("--fix")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return -1, "", "Error: ruff is not installed. Please install it via 'pip install ruff'."
    except Exception as e:
        return -1, "", f"Error running ruff: {str(e)}"

def run_ruff_format(code_dir: Path) -> tuple[int, str, str]:
    """
    Run ruff format on the specified directory.
    
    Args:
        code_dir: Path to the code directory to format
        
    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    cmd = [sys.executable, "-m", "ruff", "format", str(code_dir)]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return -1, "", "Error: ruff is not installed. Please install it via 'pip install ruff'."
    except Exception as e:
        return -1, "", f"Error running ruff format: {str(e)}"

def main():
    """Main entry point for the ruff check script."""
    project_root = Path(__file__).resolve().parent.parent.parent
    code_dir = project_root / "code"
    results_dir = project_root / "results"
    
    if not code_dir.exists():
        print(f"Error: code directory not found at {code_dir}")
        sys.exit(1)
    
    results_dir.mkdir(parents=True, exist_ok=True)
    report_path = results_dir / "ruff_check_report.json"
    
    print(f"Running ruff check on {code_dir}...")
    
    # First run: check without fixing to see initial state
    exit_code, stdout, stderr = run_ruff_check(code_dir, fix=False)
    
    if exit_code != 0:
        print("Ruff found issues. Attempting to auto-fix...")
        # Run with --fix
        exit_code_fixed, stdout_fixed, stderr_fixed = run_ruff_check(code_dir, fix=True)
        
        if exit_code_fixed != 0:
            print(f"Ruff still found {exit_code_fixed} issues after auto-fix.")
            print("Remaining issues:")
            print(stdout_fixed)
            if stderr_fixed:
                print("Errors:")
                print(stderr_fixed)
            
            # Write report even if issues remain
            report = {
                "timestamp": datetime.now().isoformat(),
                "status": "issues_remaining",
                "issues_count": exit_code_fixed,
                "output": stdout_fixed,
                "errors": stderr_fixed
            }
        else:
            print("All auto-fixable issues have been resolved.")
            report = {
                "timestamp": datetime.now().isoformat(),
                "status": "fixed",
                "issues_count": 0,
                "output": stdout_fixed,
                "errors": stderr_fixed
            }
    else:
        print("No issues found by ruff.")
        report = {
            "timestamp": datetime.now().isoformat(),
            "status": "clean",
            "issues_count": 0,
            "output": stdout,
            "errors": stderr
        }
    
    # Write report
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"Ruff check report written to {report_path}")
    
    # Also run format to ensure consistent style
    print("\nRunning ruff format...")
    exit_code_fmt, stdout_fmt, stderr_fmt = run_ruff_format(code_dir)
    
    if exit_code_fmt == 0:
        print("Format check passed.")
    else:
        print(f"Format issues found or errors occurred: {stderr_fmt}")
    
    # Final status
    if report["status"] == "clean" or report["status"] == "fixed":
        print("\nStatic analysis complete. Code is clean or has been fixed.")
        sys.exit(0)
    else:
        print("\nStatic analysis complete. Some issues could not be auto-fixed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
