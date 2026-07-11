import os
import sys
from pathlib import Path


def create_directory(path: str) -> bool:
    """
    Create a directory if it does not exist.

    Args:
        path: The path to the directory to create.

    Returns:
        True if the directory was created or already exists, False otherwise.
    """
    dir_path = Path(path)
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {path}: {e}", file=sys.stderr)
        return False


def main():
    """
    Main entry point for the directory creation script.
    Creates all required project directories based on the task list.
    """
    # Define all required directories relative to the project root
    # Assuming the script is run from the project root
    base_dir = Path(".")
    
    # Phase 1: Setup Directories
    directories = [
        base_dir / "data" / "raw",
        base_dir / "data" / "derived" / "physics_constraints",
        base_dir / "data" / "derived" / "prompts",
        base_dir / "data" / "derived" / "generated_images",
        base_dir / "data" / "derived" / "evaluation_results",
        base_dir / "data" / "processed",  # T001f target
        base_dir / "code" / "simulation",
        base_dir / "code" / "generation",
        base_dir / "code" / "evaluation",
        base_dir / "code" / "analysis",
        base_dir / "code" / "utils",
        base_dir / "tests" / "contract",
        base_dir / "tests" / "integration",
        base_dir / "tests" / "unit",
        base_dir / "specs" / "001-llmxive-followup",
        base_dir / "specs" / "001-llmxive-followup" / "contracts",
        base_dir / "state" / "projects",
    ]

    created_count = 0
    failed_count = 0

    print("Creating project directories...")
    for directory in directories:
        if create_directory(str(directory)):
            print(f"  [OK] Created: {directory}")
            created_count += 1
        else:
            print(f"  [FAIL] Failed to create: {directory}")
            failed_count += 1

    print(f"\nDirectory creation complete.")
    print(f"  Successful: {created_count}")
    print(f"  Failed: {failed_count}")

    if failed_count > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()