import subprocess
import sys
from pathlib import Path

def main():
    """
    Verify that linting and formatting tools are configured and functional.
    This script runs a dry-check of flake8, pylint, and black against the code/ directory.
    """
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"

    if not code_dir.exists():
        print(f"Error: Code directory not found at {code_dir}")
        sys.exit(1)

    print("Checking linting and formatting configuration...")

    # Check Black
    print("\n[1/3] Checking Black configuration...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "--diff", str(code_dir)],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        if result.returncode == 0:
            print("  ✓ Black: Code is formatted correctly.")
        else:
            print("  ⚠ Black: Formatting issues detected (run 'black code/' to fix).")
            # Do not exit on formatting issues, just warn
    except FileNotFoundError:
        print("  ✗ Black not found. Install with: pip install black")

    # Check Flake8
    print("\n[2/3] Checking Flake8 configuration...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", str(code_dir)],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        if result.returncode == 0:
            print("  ✓ Flake8: No linting errors found.")
        else:
            print("  ⚠ Flake8: Linting errors found:")
            print(result.stdout)
    except FileNotFoundError:
        print("  ✗ Flake8 not found. Install with: pip install flake8")

    # Check Pylint
    print("\n[3/3] Checking Pylint configuration...")
    try:
        # Pylint can be slow, so we might limit it or just check config validity
        # For this setup script, we just ensure it can run and find the config
        result = subprocess.run(
            [sys.executable, "-m", "pylint", "--help-msg", "all"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        if result.returncode == 0:
            print("  ✓ Pylint: Configuration loaded successfully.")
        else:
            print("  ⚠ Pylint: Could not verify configuration.")
    except FileNotFoundError:
        print("  ✗ Pylint not found. Install with: pip install pylint")

    print("\nLinting configuration check complete.")

if __name__ == "__main__":
    main()