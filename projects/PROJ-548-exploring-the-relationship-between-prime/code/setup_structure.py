import os
import sys
from pathlib import Path

def main():
    """
    Creates the project directory structure for PROJ-548.
    Ensures all required folders for data, analysis, utils, tests, and state exist.
    """
    # Define the project root relative to this script's location
    # The script is in code/, so root is parent of code/
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    # Define all required directories relative to project root
    required_dirs = [
        "src/data",
        "src/analysis",
        "src/utils",
        "src/cli",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/processed",
        "data/results",
        "results",
        "state",
        "figures", # Added for visualization outputs as per common pipeline needs
        "docs",    # Added for documentation
    ]

    created_count = 0
    existing_count = 0

    for dir_path_str in required_dirs:
        full_path = project_root / dir_path_str
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            existing_count += 1

    print(f"\nStructure setup complete.")
    print(f"Directories created: {created_count}")
    print(f"Directories already existing: {existing_count}")
    print(f"Project root: {project_root}")

    # Verify the structure by listing the root contents
    print("\nProject Directory Tree (Root Level):")
    for item in sorted(project_root.iterdir()):
        if item.is_dir():
            print(f"  [DIR] {item.name}/")
            # List immediate subdirs for key directories
            if item.name in ["src", "data", "tests", "results", "state"]:
                for sub in sorted(item.iterdir()):
                    if sub.is_dir():
                        print(f"    [DIR] {item.name}/{sub.name}/")

    return 0

if __name__ == "__main__":
    sys.exit(main())