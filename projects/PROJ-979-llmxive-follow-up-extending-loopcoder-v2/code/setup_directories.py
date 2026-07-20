"""
Script to initialize the project directory structure for llmXive follow-up.
Creates all required directories under projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/
"""
import os
import sys
from pathlib import Path

def main():
    """Create the project directory structure."""
    # Define the project root relative to the code directory
    # Assuming this script is run from code/ or code/scripts/
    current_dir = Path(__file__).parent
    project_root = current_dir.parent / "projects" / "PROJ-979-llmxive-follow-up-extending-loopcoder-v2"
    
    # Define all required directories
    required_dirs = [
        "data/raw",
        "data/processed",
        "code/src",
        "code/tests",
        "code/notebooks",
        "paper",
        "state",
        "contracts"
    ]
    
    # Create directories
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created: {full_path}")
    
    # Verify existence
    print("\nVerifying directory structure...")
    all_exist = True
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.is_dir():
            print(f"ERROR: Directory missing: {full_path}")
            all_exist = False
        else:
            print(f"OK: {full_path}")
    
    if all_exist:
        print("\nAll directories created successfully.")
        return 0
    else:
        print("\nSome directories failed to create.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
