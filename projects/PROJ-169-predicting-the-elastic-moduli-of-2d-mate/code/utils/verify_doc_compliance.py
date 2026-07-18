"""
Pre-flight documentation compliance check.

This script verifies that mandatory disclaimer statements are present in
README.md and docs/methodology.md before the pipeline is executed.

It is intended to be run as a pre-flight check (CI or manual) and does NOT
include this check inside the main pipeline or training scripts.

Mandatory strings to verify:
1. "This project does NOT solve the Schrödinger equation"
2. "Random seeds are pinned"
3. The Feynman quote: "Don't fool yourself — and you are the easiest person to fool"
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple

# Define the mandatory strings to search for
MANDATORY_STRINGS = [
    "This project does NOT solve the Schrödinger equation",
    "Random seeds are pinned",
    "Don't fool yourself — and you are the easiest person to fool"
]

# Define the files to check relative to the project root
FILES_TO_CHECK = [
    "README.md",
    "docs/methodology.md"
]

def find_file(base_path: Path, relative_path: str) -> Path:
    """Locate a file starting from base_path, searching upwards if needed."""
    target = base_path / relative_path
    if target.exists():
        return target

    # If not found, try searching up the directory tree (in case script is run from subdirectory)
    current = base_path
    while current != current.parent:
        candidate = current / relative_path
        if candidate.exists():
            return candidate
        current = current.parent

    return target

def check_file_for_strings(file_path: Path, strings: List[str]) -> List[Tuple[str, bool]]:
    """Check if a file contains all the mandatory strings.

    Returns a list of (string, found) tuples.
    """
    if not file_path.exists():
        return [(s, False) for s in strings]

    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return [(s, False) for s in strings]

    results = []
    for s in strings:
        found = s in content
        results.append((s, found))
    return results

def main():
    """Run the compliance check and exit with code 1 if any mandatory string is missing."""
    # Determine project root (assume script is in code/utils/)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent

    all_missing = []

    print("Running pre-flight documentation compliance check...")
    print(f"Project root: {project_root}")
    print(f"Checking files: {', '.join(FILES_TO_CHECK)}")
    print(f"Mandatory strings: {len(MANDATORY_STRINGS)}")
    print("-" * 60)

    for relative_path in FILES_TO_CHECK:
        file_path = find_file(project_root, relative_path)
        print(f"\nChecking: {relative_path} ({file_path})")

        if not file_path.exists():
            print(f"  ❌ File not found: {file_path}")
            for s in MANDATORY_STRINGS:
                all_missing.append((relative_path, s))
            continue

        results = check_file_for_strings(file_path, MANDATORY_STRINGS)
        file_has_missing = False
        for s, found in results:
            status = "✅" if found else "❌"
            print(f"  {status} '{s[:50]}...'")
            if not found:
                file_has_missing = True
                all_missing.append((relative_path, s))

        if not file_has_missing:
            print(f"  ✅ All mandatory strings found in {relative_path}")

    print("\n" + "=" * 60)

    if all_missing:
        print("❌ COMPLIANCE CHECK FAILED")
        print("The following mandatory strings are missing:")
        for file_path, missing_str in all_missing:
            print(f"  - In '{file_path}': '{missing_str}'")
        print("\nPlease update the documentation to include all mandatory disclaimers.")
        print("This script will exit with code 1 to halt the pipeline.")
        sys.exit(1)
    else:
        print("✅ COMPLIANCE CHECK PASSED")
        print("All mandatory disclaimer statements are present.")
        print("Pipeline can proceed.")
        sys.exit(0)

if __name__ == "__main__":
    main()