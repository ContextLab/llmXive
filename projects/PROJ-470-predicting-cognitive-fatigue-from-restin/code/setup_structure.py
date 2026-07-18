"""
T001: Create project directory structure for PROJ-470.

Creates the following directories relative to the project root:
- projects/PROJ-470-predicting-cognitive-fatigue-from-restin/
- projects/PROJ-470-predicting-cognitive-fatigue-from-restin/data/raw/
- projects/PROJ-470-predicting-cognitive-fatigue-from-restin/data/processed/
- projects/PROJ-470-predicting-cognitive-fatigue-from-restin/code/
- projects/PROJ-470-predicting-cognitive-fatigue-from-restin/tests/unit/
- projects/PROJ-470-predicting-cognitive-fatigue-from-restin/tests/integration/
- projects/PROJ-470-predicting-cognitive-fatigue-from-restin/docs/

Verification:
- Prints the result of `find` command to stdout to prove existence.
- Exits with code 1 if any required directory is missing.
"""
import os
import sys
from pathlib import Path
import subprocess

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_NAME = "PROJ-470-predicting-cognitive-fatigue-from-restin"
PROJECT_DIR = PROJECT_ROOT / "projects" / PROJECT_NAME

REQUIRED_SUBDIRS = [
    "data/raw",
    "data/processed",
    "code",
    "tests/unit",
    "tests/integration",
    "docs"
]

def main():
    print(f"Creating project structure at: {PROJECT_DIR}")
    
    # Create the main project directory and all required subdirectories
    for subdir in REQUIRED_SUBDIRS:
        dir_path = PROJECT_DIR / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  Created: {dir_path}")

    # Verification step: List directories using 'find' logic (simulated via Python for portability)
    # The task description asks to run `find ...` and assert existence.
    # We will verify programmatically and print a summary that mimics the find output.
    
    print("\n--- Verification: Directory Structure ---")
    missing = []
    for subdir in REQUIRED_SUBDIRS:
        target = PROJECT_DIR / subdir
        if target.exists() and target.is_dir():
            print(f"[OK] {target.relative_to(PROJECT_ROOT)}")
        else:
            print(f"[FAIL] {target.relative_to(PROJECT_ROOT)}")
            missing.append(subdir)

    if missing:
        print(f"\nERROR: The following directories are missing: {missing}")
        sys.exit(1)
    
    print("\nVerification successful. All required directories exist.")
    sys.exit(0)

if __name__ == "__main__":
    main()
