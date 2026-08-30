import subprocess
import sys
import os

def run_command(cmd):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        return False

def main():
    """Run initial linting and formatting checks on the project structure."""
    print("=== Running Linting and Formatting Checks ===")
    print("Project root:", os.path.dirname(os.path.abspath(__file__)))
    
    # Run Ruff check
    ruff_success = run_command([
        sys.executable, "-m", "ruff", "check", "."
    ])
    
    # Run Black check (dry-run)
    black_success = run_command([
        sys.executable, "-m", "black", "--check", "."
    ])
    
    if ruff_success and black_success:
        print("\n✓ All linting and formatting checks passed.")
        return 0
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())