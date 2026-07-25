"""
Setup script to create the project directory structure.
Creates: code/, data/, tests/, specs/ and their subdirectories.
"""
import os
from pathlib import Path
from config import get_project_root, get_data_dir, get_raw_data_dir, get_processed_data_dir, get_consent_dir, get_specs_dir, get_contracts_dir, get_code_dir, get_tests_dir, get_figures_dir

def create_directories():
    """Create the required project directory structure."""
    project_root = get_project_root()
    
    # Define all directories to create
    directories = [
        get_code_dir(),
        get_tests_dir(),
        get_specs_dir(),
        get_data_dir(),
        get_raw_data_dir(),
        get_processed_data_dir(),
        get_consent_dir(),
        get_contracts_dir(),
        get_figures_dir(),
        # Additional subdirectories for organization
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "consent",
        project_root / "specs" / "001-text-tone-emotional-support",
        project_root / "specs" / "001-text-tone-emotional-support" / "contracts",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        project_root / "tests" / "contract",
    ]
    
    created = []
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path.relative_to(project_root)))
        else:
            print(f"Directory already exists: {dir_path.relative_to(project_root)}")
    
    return created

def main():
    """Main entry point for the setup script."""
    print("Setting up project structure...")
    created_dirs = create_directories()
    
    if created_dirs:
        print(f"Successfully created {len(created_dirs)} directories:")
        for d in created_dirs:
            print(f"  - {d}")
    else:
        print("All directories already exist.")
    
    # Verify structure
    print("\nVerifying project structure...")
    required_dirs = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/consent",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "specs",
        "specs/001-text-tone-emotional-support",
        "specs/001-text-tone-emotional-support/contracts",
    ]
    
    project_root = get_project_root()
    all_good = True
    for rel_dir in required_dirs:
        full_path = project_root / rel_dir
        if not full_path.exists():
            print(f"ERROR: Missing directory: {rel_dir}")
            all_good = False
        else:
            print(f"OK: {rel_dir}")
    
    if all_good:
        print("\nProject structure setup complete.")
    else:
        print("\nProject structure setup failed.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
