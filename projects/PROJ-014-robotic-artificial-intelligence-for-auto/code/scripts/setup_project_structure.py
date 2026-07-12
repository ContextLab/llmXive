"""
Script to initialize the project directory structure for the Robotic AI Sensory Fidelity Ablation Study.
Creates all required directories under the 'code/' folder as per the implementation plan.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the project directory structure."""
    # Define the base directory for the project code
    base_dir = Path(__file__).resolve().parent.parent  # code/
    
    # Define the directory structure to create
    directories = [
        # Source subdirectories
        "src/environment",
        "src/data",
        "src/agents",
        "src/analysis",
        "src/utils",
        
        # Top-level tool directories
        "scripts",
        "tests",
        
        # Data and results storage
        "data",
        "results"
    ]
    
    created_count = 0
    skipped_count = 0
    
    print(f"Initializing project structure at: {base_dir}")
    
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {full_path}")
            created_count += 1
        else:
            skipped_count += 1
    
    print(f"\nStructure initialization complete.")
    print(f"  Created: {created_count} directories")
    print(f"  Skipped (existing): {skipped_count} directories")
    
    # Verify critical paths exist
    critical_paths = [
        "src/environment",
        "src/data",
        "src/agents",
        "src/analysis",
        "src/utils",
        "scripts",
        "tests",
        "data",
        "results"
    ]
    
    all_present = True
    for cp in critical_paths:
        if not (base_dir / cp).exists():
            print(f"ERROR: Critical path missing: {base_dir / cp}")
            all_present = False
    
    if all_present:
        print("SUCCESS: All required directories are present.")
        return 0
    else:
        print("FAILURE: Some required directories are missing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())