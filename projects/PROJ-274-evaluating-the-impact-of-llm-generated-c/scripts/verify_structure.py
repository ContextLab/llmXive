"""
T001b: Verify project directory structure.
Asserts existence of key directories and exits with code 0 on success.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root based on the standard llmXive layout
    # The script is expected to be run from the project root:
    # projects/PROJ-274-evaluating-the-impact-of-llm-generated-c/
    project_root = Path(__file__).parent.parent

    required_dirs = [
        "data/raw",
        "data/processed",
        "data/reports",
        "data/logs",
        "code",
        "code/utils",
        "code/experiment",
        "code/analysis",
        "code/generation",
        "code/recruitment",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "specs",
        "state",
        "config",
        "contracts",
    ]

    missing_dirs = []

    print(f"Verifying structure in: {project_root}")

    for rel_path in required_dirs:
        full_path = project_root / rel_path
        if not full_path.is_dir():
            missing_dirs.append(rel_path)
            print(f"MISSING: {full_path}")
        else:
            print(f"OK: {full_path}")

    if missing_dirs:
        print(f"\nERROR: {len(missing_dirs)} required directories are missing.")
        print("Please ensure T001a (Create project directory structure) has been completed.")
        sys.exit(1)

    print("\nAll required directories exist. Structure verification passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()