"""
Script to run ruff check for print statements (T20) across the codebase.
This implements Task T036: Ensure no print statements remain in the codebase.
"""
import subprocess
import sys
from pathlib import Path

def main():
    project_root = Path(__file__).parent.parent.parent
    code_dir = project_root / "code"

    # Run ruff check for T20 (print statements)
    try:
        result = subprocess.run(
            [
                sys.executable, "-m", "ruff", "check", 
                "--select=T20", 
                str(code_dir)
            ],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            print("✓ No print statements found (T20 check passed)")
            sys.exit(0)
        else:
            print("✗ Print statements detected (T20 violations):")
            print(result.stdout)
            if result.stderr:
                print("Errors:", result.stderr)
            sys.exit(1)
    except FileNotFoundError:
        print("✗ ruff not found. Install it via: pip install ruff")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error running ruff check: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
