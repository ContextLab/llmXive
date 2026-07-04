"""
Script to initialize the project directory structure for the 
'Influence of Chatbot Politeness on User-Perceived Quality' research project.

Creates the following directories relative to the project root:
- data/raw
- data/processed
- code
- code/utils
- tests
- tests/unit
- tests/integration
- tests/contract
- docs
- specs
- figures

Also creates .gitkeep files in data directories to ensure they are tracked
by git even when empty.
"""
import os
import sys
from pathlib import Path

def create_structure():
    # Define the root directory (current working directory where script is run)
    root = Path.cwd()
    
    # Define the directory structure to create
    # Using relative paths from the root
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "code/utils",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "docs",
        "specs",
        "figures"
    ]
    
    # Track created directories
    created = []
    
    for dir_path in directories:
        full_path = root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(dir_path)
            
            # Create .gitkeep in data directories to ensure they are tracked
            if dir_path.startswith("data/"):
                gitkeep_path = full_path / ".gitkeep"
                if not gitkeep_path.exists():
                    gitkeep_path.touch()
                    print(f"  Created .gitkeep in {dir_path}")
                    
        except PermissionError:
            print(f"  Error: Permission denied creating {dir_path}")
            return False
        except Exception as e:
            print(f"  Error creating {dir_path}: {e}")
            return False
    
    # Print summary
    print(f"\nProject structure initialized successfully in: {root}")
    print(f"Created {len(created)} directories:")
    for d in created:
        print(f"  - {d}")
        
    return True

if __name__ == "__main__":
    print("Initializing project structure for PROJ-755...")
    success = create_structure()
    if not success:
        print("\nInitialization failed. Please check permissions and try again.")
        sys.exit(1)
    else:
        print("\nInitialization complete.")
        sys.exit(0)