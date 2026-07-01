import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required project directory structure for PROJ-478.
    
    This function implements Task T001a by creating the following directories:
    - code/src/ (and subdirectories: data, modeling, analysis, utils)
    - code/data/ (and subdirectories: raw, processed, metadata)
    - code/results/
    - code/tests/ (and subdirectories: unit, integration, contract)
    
    It also ensures that each directory contains a .gitkeep file to ensure
    the directories are tracked by git.
    """
    base_path = Path("code")
    
    # Define directory structure based on T001a, T001b, T001c
    directories = [
        # Source code structure (T001a)
        "src",
        "src/data",
        "src/modeling",
        "src/analysis",
        "src/utils",
        
        # Data structure (T001b)
        "data/raw",
        "data/processed",
        "data/metadata",
        
        # Results structure (T001b)
        "results",
        
        # Test structure (T001c)
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]
    
    created_count = 0
    skipped_count = 0
    
    for dir_path in directories:
        full_path = base_path / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            
            # Create .gitkeep to ensure directory is tracked
            gitkeep_path = full_path / ".gitkeep"
            if not gitkeep_path.exists():
                gitkeep_path.touch()
            
            print(f"Created directory: {full_path}")
            created_count += 1
        except OSError as e:
            print(f"Error creating directory {full_path}: {e}", file=sys.stderr)
            return False
    
    print(f"\nDirectory creation complete.")
    print(f"Directories created: {created_count}")
    print(f"Directories skipped (already exist): {skipped_count}")
    print(f"\nStructure created under: {base_path.absolute()}")
    
    return True

if __name__ == "__main__":
    success = create_directories()
    sys.exit(0 if success else 1)
