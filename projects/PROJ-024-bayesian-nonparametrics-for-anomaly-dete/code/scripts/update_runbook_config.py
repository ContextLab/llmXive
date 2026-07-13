"""
Script to update the run-book (quickstart.md) to reference the correct config script.

This script ensures that the quickstart.md file references the existing config.py
script at code/src/config.py instead of any non-existent paths.
"""

import os
import sys
from pathlib import Path

# Project root is parent of code/
PROJECT_ROOT = Path(__file__).parent.parent.parent
QUICKSTART_PATH = PROJECT_ROOT / "quickstart.md"

def update_runbook():
    """Update quickstart.md to reference the correct config script."""
    if not QUICKSTART_PATH.exists():
        print(f"WARNING: quickstart.md not found at {QUICKSTART_PATH}")
        print("Creating a note that the run-book should reference code/src/config.py")
        return False

    with open(QUICKSTART_PATH, 'r') as f:
        content = f.read()

    # Check if the correct reference already exists
    correct_reference = "python code/src/config.py --check"
    if correct_reference in content:
        print("✓ Run-book already references the correct config script")
        return True

    # Check for incorrect references
    incorrect_references = [
        "python code/config.py",
        "python code/config.py --check",
        "python src/config.py",
        "python src/config.py --check"
    ]

    needs_update = False
    for ref in incorrect_references:
        if ref in content:
            print(f"Found incorrect reference: {ref}")
            needs_update = True

    if needs_update:
        print("Updating run-book to reference correct config script...")
        # Replace incorrect references with correct one
        for ref in incorrect_references:
            content = content.replace(ref, correct_reference)

        with open(QUICKSTART_PATH, 'w') as f:
            f.write(content)

        print(f"✓ Updated {QUICKSTART_PATH}")
        print(f"  Now references: {correct_reference}")
        return True
    else:
        print("No incorrect references found, but correct reference also not present")
        print("Manual update may be needed to add: python code/src/config.py --check")
        return False

def main():
    """CLI entry point."""
    success = update_runbook()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())