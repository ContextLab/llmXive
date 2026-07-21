"""
T035b: Run black --check on code/ and verify exit code 0.

This script invokes the black formatter in check mode against the 'code/' directory.
It exits with code 0 if all files are properly formatted, or code 1 if formatting
issues are found or black encounters an error.
"""
import subprocess
import sys
from pathlib import Path

def run_black_check():
    """Run black --check on the code/ directory."""
    root_dir = Path(__file__).resolve().parent.parent
    code_dir = root_dir / "code"

    if not code_dir.exists():
        print(f"Error: code/ directory not found at {code_dir}")
        return 1

    try:
        result = subprocess.run(
            ["black", "--check", "--quiet", str(code_dir)],
            cwd=root_dir,
            capture_output=True,
            text=True,
        )
        
        if result.returncode == 0:
            print("Black check passed: All files are properly formatted.")
            return 0
        else:
            print("Black check failed: Formatting issues detected.")
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)
            return 1
            
    except FileNotFoundError:
        print("Error: 'black' command not found. Please install it via 'pip install black'.")
        return 1
    except Exception as e:
        print(f"Error running black check: {e}")
        return 1

def main():
    sys.exit(run_black_check())

if __name__ == "__main__":
    main()