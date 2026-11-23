"""
Ruff fix runner for the material strength prediction project.
Executes 'ruff check --fix' on the code/ directory and verifies exit code 0.
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    """Run ruff check --fix and verify success."""
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"

    if not code_dir.exists():
        print(f"Error: code directory not found at {code_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Running ruff check --fix on {code_dir}...")
    
    try:
        result = subprocess.run(
            ["ruff", "check", "--fix", str(code_dir)],
            cwd=project_root,
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ Ruff check --fix completed successfully (exit code 0).")
            sys.exit(0)
        else:
            print(f"✗ Ruff check --fix failed with exit code {result.returncode}", file=sys.stderr)
            print("Note: Some issues may require manual fixes or are unfixable.", file=sys.stderr)
            sys.exit(result.returncode)
            
    except FileNotFoundError:
        print("Error: 'ruff' command not found. Please install it via 'pip install ruff'.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error running ruff: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
