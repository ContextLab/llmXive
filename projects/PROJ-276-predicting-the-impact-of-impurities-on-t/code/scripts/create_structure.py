import os
from pathlib import Path

def main():
    """
    Creates the project directory structure for PROJ-276.
    This script ensures all required folders exist as per the implementation plan.
    """
    project_root = Path(__file__).resolve().parent.parent
    base_dirs = [
        "src/ingestion",
        "src/modeling",
        "src/visualization",
        "src/utils",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "data/raw",
        "data/processed",
        "docs"
    ]

    created_count = 0
    for dir_path in base_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path.relative_to(project_root)}")
            created_count += 1
        else:
            # Even if it exists, we consider it part of the structure
            pass

    print(f"Project structure verification complete. {created_count} new directories created.")
    print(f"Base path: {project_root}")

    # Verify structure by listing
    print("\n--- Directory Structure Verification ---")
    for dir_path in base_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"[OK] {full_path.relative_to(project_root)}")
        else:
            print(f"[MISSING] {full_path.relative_to(project_root)}")
    print("--- End Verification ---")

if __name__ == "__main__":
    main()
