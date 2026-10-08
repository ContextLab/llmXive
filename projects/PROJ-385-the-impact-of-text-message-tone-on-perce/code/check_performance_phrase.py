"""
Check Performance Documentation Alignment (T099c).

Verifies that both 'plan.md' and 'README.md' contain the exact phrase
"≤ 6 hours" to ensure performance documentation is aligned.
"""

import sys
from pathlib import Path

# Target phrase to search for
TARGET_PHRASE = "≤ 6 hours"

# Files to check (relative to project root)
FILES_TO_CHECK = [
    "plan.md",
    "README.md"
]

def check_file_for_phrase(file_path: Path, phrase: str) -> bool:
    """
    Check if a file contains the target phrase.

    Args:
        file_path: Path to the file to check.
        phrase: The exact phrase to search for.

    Returns:
        True if the phrase is found, False otherwise.
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        return phrase in content
    except FileNotFoundError:
        print(f"ERROR: File not found: {file_path}")
        return False
    except Exception as e:
        print(f"ERROR: Failed to read {file_path}: {e}")
        return False

def main():
    """Main entry point for the performance phrase check."""
    # Determine project root (assume script is in code/, root is parent)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    all_found = True

    for filename in FILES_TO_CHECK:
        file_path = project_root / filename
        print(f"Checking {filename} for phrase: '{TARGET_PHRASE}'...")

        if check_file_for_phrase(file_path, TARGET_PHRASE):
            print(f"  ✓ Found in {filename}")
        else:
            print(f"  ✗ NOT found in {filename}")
            all_found = False

    if all_found:
        print("\n✓ All documentation files contain the required performance phrase.")
        sys.exit(0)
    else:
        print(f"\n✗ FAILURE: The phrase '{TARGET_PHRASE}' is missing from one or more files.")
        print("Please update 'plan.md' and 'README.md' to include this phrase.")
        sys.exit(1)

if __name__ == "__main__":
    main()
