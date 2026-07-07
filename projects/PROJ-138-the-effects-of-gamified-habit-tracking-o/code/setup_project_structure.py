import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required project directory structure for the llmXive pipeline.
    Directories created:
    - code/data, code/analysis, code/reports, code/utils, code/tests
    - data/raw, data/processed, data/consent
    """
    base_dir = Path(__file__).resolve().parent.parent
    
    # Define required directories relative to project root
    directories = [
        "code/data",
        "code/analysis",
        "code/reports",
        "code/utils",
        "code/tests",
        "data/raw",
        "data/processed",
        "data/consent",
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        
        # Create .gitkeep to ensure directory is tracked by git
        gitkeep_path = full_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            created_count += 1
        
        print(f"Verified/Created: {full_path}")
    
    print(f"\nProject structure ready. Created {created_count} new .gitkeep files.")
    return True

def verify_structure():
    """
    Verifies that all required directories exist and contain .gitkeep files.
    Returns True if all checks pass, False otherwise.
    """
    base_dir = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        "code/data",
        "code/analysis",
        "code/reports",
        "code/utils",
        "code/tests",
        "data/raw",
        "data/processed",
        "data/consent",
    ]
    
    all_good = True
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        if not full_path.exists():
            print(f"ERROR: Directory missing: {full_path}")
            all_good = False
            continue
        
        gitkeep_path = full_path / ".gitkeep"
        if not gitkeep_path.exists():
            print(f"WARNING: Missing .gitkeep in: {full_path}")
            # Create it to fix the state
            gitkeep_path.touch()
            print(f"  -> Created missing .gitkeep")
        
        if not full_path.is_dir():
            print(f"ERROR: Path is not a directory: {full_path}")
            all_good = False
    
    return all_good

def main():
    """
    Entry point for the setup script.
    Creates directories and verifies the structure.
    """
    print("Initializing project directory structure...")
    create_directories()
    
    print("\nVerifying structure...")
    if verify_structure():
        print("SUCCESS: All required directories and .gitkeep files are present.")
        return 0
    else:
        print("FAILURE: Verification failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())