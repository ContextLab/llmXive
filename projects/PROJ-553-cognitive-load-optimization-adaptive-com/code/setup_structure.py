import os
from pathlib import Path

def main():
    """
    Creates the required project directory structure for the Cognitive Load Optimization project.
    This script ensures all necessary folders exist to support data storage, code organization,
    and documentation as defined in task T001a.
    """
    # Define the base directory (project root)
    base_dir = Path(__file__).resolve().parent.parent

    # Define the required directories relative to the project root
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/explanation_tiers",
        "data/simulation_results",
        "code",
        "tests",
        "docs"
    ]

    created_count = 0
    existing_count = 0

    print(f"Project root detected at: {base_dir}")
    print("Verifying directory structure...")

    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {full_path}")
            created_count += 1
        else:
            existing_count += 1

    print(f"\nDirectory structure verification complete.")
    print(f"  New directories created: {created_count}")
    print(f"  Existing directories found: {existing_count}")
    print(f"  Total directories ensured: {created_count + existing_count}")

    # Verify the specific directories required by T001a
    mandatory_dirs = [
        "data/raw",
        "data/processed",
        "data/explanation_tiers",
        "data/simulation_results",
        "code",
        "tests",
        "docs"
    ]

    all_present = True
    for d in mandatory_dirs:
        if not (base_dir / d).exists():
            print(f"ERROR: Mandatory directory missing: {base_dir / d}")
            all_present = False

    if all_present:
        print("\nSUCCESS: All required directories for T001a are present.")
    else:
        print("\nFAILURE: Some required directories are missing.")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())