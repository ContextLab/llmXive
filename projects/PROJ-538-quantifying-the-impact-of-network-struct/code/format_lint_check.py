import subprocess
import sys
from pathlib import Path

def run_command(cmd):
    """Run a shell command and return the result."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result

def main():
    """
    Check and format code using ruff and black.
    
    This satisfies the requirement for T003 (linting and formatting configuration).
    """
    base_dir = Path(__file__).resolve().parent.parent
    code_dir = base_dir / "code"
    
    # Install dependencies if not present
    print("Installing linting and formatting tools...")
    run_command(f"{sys.executable} -m pip install ruff black --quiet")
    
    # Format with black
    print("Running black formatter...")
    result = run_command(f"black {code_dir}")
    if result.returncode == 0:
        print("Black formatting successful.")
    else:
        print(f"Black formatting failed: {result.stderr}")
    
    # Lint with ruff
    print("Running ruff linter...")
    result = run_command(f"ruff check {code_dir}")
    if result.returncode == 0:
        print("Ruff linting successful.")
    else:
        print(f"Ruff linting found issues: {result.stdout}")
    
    # Generate report
    report_path = base_dir / "data" / "lint_report.txt"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        f.write("Linting and Formatting Report\n")
        f.write("=" * 40 + "\n")
        f.write(f"Black: {'Success' if result.returncode == 0 else 'Issues Found'}\n")
        f.write(f"Ruff: {'Success' if result.returncode == 0 else 'Issues Found'}\n")
    
    print(f"Report saved to {report_path}")
    return 0
