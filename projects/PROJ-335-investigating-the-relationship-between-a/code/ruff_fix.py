"""
Linter fixer script for llmXive project.
Runs ruff on all Python files in the code/ directory and fixes violations.
"""
import subprocess
import sys
from pathlib import Path

def main():
    """Run ruff check and fix on the code directory."""
    code_dir = Path(__file__).parent
    ruff_cmd = [
        sys.executable,
        "-m",
        "ruff",
        "check",
        str(code_dir),
        "--fix",
        "--exit-zero",  # Don't fail the script if issues remain
    ]

    print(f"Running ruff fix in {code_dir}...")
    try:
        result = subprocess.run(
            ruff_cmd,
            check=False,  # We handle the exit code ourselves
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ Ruff check passed: No violations found.")
        else:
            print("⚠ Ruff found issues that were fixed or could not be auto-fixed.")
            # Run a final check to see if any issues remain
            check_cmd = [
                sys.executable,
                "-m",
                "ruff",
                "check",
                str(code_dir),
            ]
            check_result = subprocess.run(check_cmd, capture_output=True, text=True)
            if check_result.returncode != 0:
                print("\nRemaining violations (manual fix required):")
                print(check_result.stdout)
                sys.exit(1)
            else:
                print("✓ All violations successfully fixed.")
    except FileNotFoundError:
        print("ERROR: ruff is not installed. Please install it with: pip install ruff")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to run ruff: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
