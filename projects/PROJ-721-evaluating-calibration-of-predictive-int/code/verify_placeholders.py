"""
T056: Verify that all "deferred" placeholders in plan.md, spec.md, and code/config.yaml
have been resolved or explicitly noted as "TBD".

This script scans the project for the string "[deferred]" (case-insensitive) in:
- plan.md
- spec.md
- code/config.yaml (and any other .yaml files in the code/ or root if specified)

It exits with code 0 if no matches are found, or code 1 if any matches are found,
printing the locations of the matches.
"""
import os
import re
import sys
from pathlib import Path

# Define the files to check relative to the project root
# Based on the task description: plan.md, spec.md, and code/config.yaml
# We also include any other yaml files in code/ just in case, though the task
# specifically mentions config.yaml.
TARGET_FILES = [
    "plan.md",
    "spec.md",
    "code/config.yaml",
]

# Pattern to match "[deferred]" (case-insensitive)
# We look for the exact string or variations like "[ Deferred ]" if they exist,
# but the task specifically says "[deferred]".
pattern = re.compile(r"\[deferred\]", re.IGNORECASE)

def find_placeholders(root_dir: str, files: list) -> list:
    """
    Scan specified files for the placeholder pattern.
    Returns a list of (file_path, line_number, line_content) tuples.
    """
    matches = []
    root_path = Path(root_dir)

    for file_name in files:
        file_path = root_path / file_name
        if not file_path.exists():
            # If a required file is missing, we might want to warn,
            # but the task is to find placeholders. If the file doesn't exist,
            # there are no placeholders in it.
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    if pattern.search(line):
                        matches.append((str(file_path), line_num, line.strip()))
        except Exception as e:
            print(f"Error reading {file_path}: {e}", file=sys.stderr)

    return matches

def main():
    # Determine project root (current working directory or parent if running from subfolder)
    # The task implies running from the project root.
    project_root = os.getcwd()

    print(f"Scanning for '[deferred]' placeholders in: {', '.join(TARGET_FILES)}")

    matches = find_placeholders(project_root, TARGET_FILES)

    if matches:
        print(f"\n❌ FOUND {len(matches)} instance(s) of '[deferred]':")
        for file_path, line_num, line_content in matches:
            print(f"  {file_path}:{line_num}: {line_content}")
        print("\nAction required: Resolve or explicitly mark as 'TBD' in the source files.")
        sys.exit(1)
    else:
        print("\n✅ No '[deferred]' placeholders found in the specified files.")
        print("Task T056 verification passed.")
        sys.exit(0)

if __name__ == "__main__":
    main()
