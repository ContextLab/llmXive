"""
Utility script to run formatting and linting checks.
Ensures code meets project standards before committing.
"""
import subprocess
import sys
import os

def run_command(cmd: list[str]) -> int:
    """Run a shell command and return its exit code."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"Command failed: {' '.join(cmd)}")
    return result.returncode

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root_dir)

    # Check if dependencies are installed
    try:
        import black
        import ruff
    except ImportError:
        print("Error: Formatting dependencies not installed. Run: pip install -r requirements.txt")
        return 1

    # Run Ruff (Linting + Auto-fix)
    print("\n--- Running Ruff Linter (Auto-fix) ---")
    ret = run_command(["ruff", "check", "code/", "tests/", "--fix"])
    if ret != 0:
        print("Ruff found errors that could not be auto-fixed.")
        return ret

    # Run Ruff (Format check - optional, black handles formatting)
    # We rely on black for formatting, but ruff can check for style issues too.
    
    # Run Black (Formatting)
    print("\n--- Running Black Formatter ---")
    ret = run_command(["black", "code/", "tests/", "--check"])
    if ret != 0:
        print("Code is not formatted. Run 'python scripts/format.py --fix' to fix.")
        return ret

    print("\n✅ All checks passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
