import os
from pathlib import Path
from setup_directories import create_directories

def main():
    """
    Orchestrates the setup of the entire data and state directory structure.
    This script is the entry point for Task T004.
    """
    print("Initializing data and state directory structure for PROJ-526...")
    
    # Delegate to the core directory creation logic
    created_count = create_directories()
    
    print(f"Setup complete. {created_count} directories created/verified.")
    print("Paths ready:")
    print(f"  - data/raw/")
    print(f"  - data/processed/")
    print(f"  - state/")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
