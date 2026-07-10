"""
Verification script for T001: Project Structure Creation.
Asserts that the required directory tree exists under the project root.
"""
import os
import sys
from pathlib import Path

def main():
    # Determine the project root based on the script location
    # Script is at: projects/PROJ-274-evaluating-the-impact-of-llm-generated-c/scripts/verify_structure.py
    # Project root is the parent of 'scripts'
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent

    required_dirs = [
        "data/raw",
        "data/processed",
        "data/reports",
        "code",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "specs"
    ]

    all_passed = True

    print(f"Verifying project structure at: {project_root}")

    for rel_path in required_dirs:
        full_path = project_root / rel_path
        if not full_path.is_dir():
            print(f"FAIL: Missing directory: {full_path}")
            all_passed = False
        else:
            print(f"OK: Found directory: {full_path}")

    # Specific assertions requested in task description
    assert (project_root / "data/raw").is_dir(), "data/raw directory missing"
    assert (project_root / "code").is_dir(), "code directory missing"
    assert (project_root / "tests").is_dir(), "tests directory missing"

    if all_passed:
        print("\nVerification successful: All required directories exist.")
        sys.exit(0)
    else:
        print("\nVerification failed: Some directories are missing.")
        sys.exit(1)

if __name__ == "__main__":
    main()