"""
Directory Setup for llmXive Project PROJ-027
Creates the standard pipeline directory structure and verifies existence.
"""
import os
import sys
from pathlib import Path

# Define the directories to create relative to the project root
DIRECTORIES = [
    "code/01_ingest",
    "code/02_process",
    "code/03_model",
    "code/04_validate",
    "code/05_viz",
]

def create_directories(base_path: Path) -> int:
    """
    Create the required directories if they do not exist.
    Returns the number of directories created.
    """
    created_count = 0
    for dir_name in DIRECTORIES:
        target_dir = base_path / dir_name
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)
            created_count += 1
    return created_count

def verify_directories(base_path: Path) -> bool:
    """
    Verify that all required directories exist.
    Prints verification status to stdout.
    """
    all_exist = True
    missing = []
    for dir_name in DIRECTORIES:
        target_dir = base_path / dir_name
        if target_dir.exists():
            print(f"✓ Directory exists: {dir_name}")
        else:
            print(f"✗ Directory missing: {dir_name}")
            all_exist = False
            missing.append(dir_name)
    
    if not all_exist:
        print(f"\nError: {len(missing)} directories are missing.")
        return False
    
    print(f"\nSuccess: All {len(DIRECTORIES)} directories verified.")
    return True

def main():
    """Main entry point for directory setup."""
    # Determine project root (parent of 'code' directory)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent

    print(f"Project Root: {project_root}")
    print(f"Creating directories under: {project_root}")

    created = create_directories(project_root)
    if created > 0:
        print(f"Created {created} new directories.")
    
    is_valid = verify_directories(project_root)
    
    if not is_valid:
        sys.exit(1)

if __name__ == "__main__":
    main()