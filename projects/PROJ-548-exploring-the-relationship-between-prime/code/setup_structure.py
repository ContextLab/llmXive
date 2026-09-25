import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure for PROJ-548.
    Addresses FR-001 (Project Setup) and SC-004 (Directory Structure).
    """
    base_dir = Path.cwd()
    
    # Define all required directories relative to project root
    directories = [
        # Source code structure
        "src/data",
        "src/analysis",
        "src/utils",
        "src/cli",
        
        # Test structure
        "tests/unit",
        "tests/integration",
        
        # Data structure
        "data/raw",
        "data/processed",
        "data/results",
        
        # Results and state
        "results",
        "state"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory exists: {full_path}")
    
    print(f"\nProject structure setup complete. {created_count} new directories created.")
    print("Directories created:")
    for dir_path in directories:
        print(f"  - {dir_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())