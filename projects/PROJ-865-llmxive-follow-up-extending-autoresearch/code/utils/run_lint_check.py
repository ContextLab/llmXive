"""
Task T035a: Run `ruff --check` on `code/` and verify exit code 0.

This script executes the ruff linter against the project's code directory.
It exits with code 0 if linting passes, or non-zero if issues are found.
"""
import subprocess
import sys
from pathlib import Path

def main():
    """Run ruff check on the code directory."""
    project_root = Path(__file__).resolve().parent.parent.parent
    code_dir = project_root / "code"
    
    if not code_dir.exists():
        print(f"ERROR: Code directory not found at {code_dir}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Running ruff check on {code_dir}...")
    
    try:
        result = subprocess.run(
            ["ruff", "check", str(code_dir)],
            cwd=project_root,
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print("SUCCESS: ruff check passed (exit code 0)")
            sys.exit(0)
        else:
            print(f"FAILURE: ruff check found issues (exit code {result.returncode})", file=sys.stderr)
            sys.exit(result.returncode)
            
    except FileNotFoundError:
        print("ERROR: 'ruff' command not found. Please install it via: pip install ruff", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to run ruff: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
