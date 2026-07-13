"""
Utility to run linting and formatting checks as a script.
"""
import sys
from pathlib import Path

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.linting_config import (
    run_black_check,
    run_black_format,
    run_flake8,
    run_isort_check,
    run_isort_format
)

def main():
    """Main entry point for linting runner."""
    if len(sys.argv) < 2:
        print("Usage: python -m code.utils.linting_runner [check|format]")
        print("  check  : Run all checks (black, flake8, isort)")
        print("  format : Format code with black and isort")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "check":
        print("Running linting checks...")
        success = True

        print("Checking Black formatting...")
        if not run_black_check():
            print("  ❌ Black check failed")
            success = False
        else:
            print("  ✅ Black check passed")

        print("Checking Isort...")
        if not run_isort_check():
            print("  ❌ Isort check failed")
            success = False
        else:
            print("  ✅ Isort check passed")

        print("Running Flake8...")
        if not run_flake8():
            print("  ❌ Flake8 check failed")
            success = False
        else:
            print("  ✅ Flake8 check passed")

        if success:
            print("\n✅ All linting checks passed!")
            sys.exit(0)
        else:
            print("\n❌ Some linting checks failed.")
            sys.exit(1)

    elif command == "format":
        print("Formatting code...")
        success = True

        print("Running Black...")
        if not run_black_format():
            print("  ❌ Black formatting failed")
            success = False
        else:
            print("  ✅ Black formatting completed")

        print("Running Isort...")
        if not run_isort_format():
            print("  ❌ Isort formatting failed")
            success = False
        else:
            print("  ✅ Isort formatting completed")

        if success:
            print("\n✅ Code formatted successfully!")
            sys.exit(0)
        else:
            print("\n❌ Some formatting steps failed.")
            sys.exit(1)
    else:
        print(f"Unknown command: {command}")
        print("Use 'check' or 'format'")
        sys.exit(1)

if __name__ == "__main__":
    main()