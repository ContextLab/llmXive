"""
Utility script to run linting and formatting checks.
Usage: python code/lint_check.py
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str]) -> int:
    """Run a command and return the exit code."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)
    return result.returncode

def main():
    root = Path(__file__).parent.parent
    code_dir = root / "code"
    tests_dir = root / "tests"
    
    # Check if ruff and black are installed
    try:
        import ruff
        import black
    except ImportError:
        print("Error: ruff and black are required. Install them with: pip install ruff black")
        sys.exit(1)
    
    exit_code = 0
    
    # Run Ruff Check
    print("\n--- Running Ruff Check ---")
    if run_command(["ruff", "check", str(code_dir), str(tests_dir)]) != 0:
        exit_code = 1
    
    # Run Ruff Format (check only)
    print("\n--- Running Ruff Format Check (simulating Black) ---")
    # Ruff format is the new standard, but we check against black config if needed
    # Here we use ruff format --check as the modern equivalent
    if run_command(["ruff", "format", "--check", str(code_dir), str(tests_dir)]) != 0:
        print("Note: Formatting differences found. Run 'ruff format' to fix.")
        exit_code = 1
    
    if exit_code == 0:
        print("\n✅ All checks passed!")
    else:
        print("\n❌ Some checks failed.")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()