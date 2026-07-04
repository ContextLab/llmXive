"""
T001: Create project structure per implementation plan.
This script initializes the directory structure for PROJ-062.
It creates the necessary folders under `projects/PROJ-062-quantifying-the-impact-of-code-ownership/`
and ensures the `code/`, `data/`, `tests/`, and `docs/` roots exist.
"""
import os
import sys
from pathlib import Path

def create_structure():
    # Determine project root relative to this script's location
    # Assuming script is at projects/PROJ-062/code/setup_project.py
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    proj_name = "PROJ-062-quantifying-the-impact-of-code-ownership"
    
    # Base path for the project workspace
    base_path = project_root / proj_name
    
    # Define the directory structure to create
    # Based on tasks.md Phase 1 & 2 requirements
    directories = [
        # Core project roots
        "code",
        "data",
        "tests",
        "docs",
        "specs",
        "logs",
        "state",
        
        # Data subdirectories (Phase 2)
        "data/raw",
        "data/intermediate",
        "data/results",
        
        # Test subdirectories (Phase 2)
        "tests/contract",
        "tests/integration",
        "tests/unit",
        
        # Specs subdirectory for the specific feature (Phase 2)
        "specs/001-code-ownership-analysis",
        "specs/001-code-ownership-analysis/contracts",
    ]
    
    created_count = 0
    skipped_count = 0
    
    print(f"Initializing project structure at: {base_path}")
    
    for dir_path in directories:
        full_path = base_path / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            if full_path.is_dir():
                # Create a .gitkeep file to ensure directories are tracked by git
                keep_file = full_path / ".gitkeep"
                if not keep_file.exists():
                    keep_file.write_text("# Keep this directory\n")
                created_count += 1
                print(f"  Created: {dir_path}")
            else:
                print(f"  Exists (file?): {dir_path}")
        except OSError as e:
            print(f"  Error creating {dir_path}: {e}")
            skipped_count += 1
    
    print(f"\nStructure initialization complete.")
    print(f"  Directories created: {created_count}")
    print(f"  Skipped/Errors: {skipped_count}")
    
    # Verify specific critical paths required by later tasks
    critical_paths = [
        "data/intermediate",
        "data/results",
        "code",
        "tests/unit",
        "specs/001-code-ownership-analysis/contracts"
    ]
    
    missing = []
    for p in critical_paths:
        if not (base_path / p).exists():
            missing.append(p)
    
    if missing:
        print(f"\n⚠️  WARNING: Critical paths missing: {missing}")
        return False
    
    print("All critical paths verified.")
    return True

if __name__ == "__main__":
    success = create_structure()
    sys.exit(0 if success else 1)
