import os
import sys
from pathlib import Path

def create_directory_structure(base_dir: str) -> None:
    """
    Create the required project directory structure for PROJ-874.
    
    Creates:
    - code/
    - data/raw/
    - data/processed/
    - data/results/
    - tests/
    - docs/
    - contracts/
    
    Args:
        base_dir: The root directory where the project structure will be created.
    """
    project_root = Path(base_dir)
    
    # Define the required directories relative to the project root
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "tests",
        "docs",
        "contracts"
    ]
    
    created_count = 0
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"\nProject structure verification complete.")
    print(f"Base directory: {project_root}")
    print(f"Total directories created in this run: {created_count}")
    
    # Verify structure by listing all created directories
    print("\nVerifying directory structure:")
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists() and dir_path.is_dir():
            print(f"  [OK] {dir_path}")
        else:
            print(f"  [FAIL] {dir_path} - does not exist or is not a directory")
            raise RuntimeError(f"Directory verification failed for {dir_path}")
    
    print("\nAll required directories verified successfully.")

def main():
    """Main entry point for the project structure setup script."""
    # Default to the project root relative to this script's location
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent  # Go up one level from code/ to project root
    
    # Allow override via command line argument
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1]).resolve()
    
    print(f"Setting up project structure at: {project_root}")
    create_directory_structure(str(project_root))
    print("\nSetup complete. Run 'ls -R' to inspect the structure.")

if __name__ == "__main__":
    main()