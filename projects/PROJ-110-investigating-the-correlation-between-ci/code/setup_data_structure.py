"""
Standalone script to initialize the data directory structure and contracts.
Run this script to ensure the project environment is correctly set up.
"""
import sys
from pathlib import Path
from setup_structure import create_directories

def main():
    root = Path(__file__).parent.parent
    print(f"Initializing data structure in: {root}")
    create_directories(root)
    
    # Verify creation
    required_dirs = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "contracts",
    ]
    
    all_ok = True
    for d in required_dirs:
        if not d.exists():
            print(f"ERROR: Missing directory {d}")
            all_ok = False
        else:
            print(f"OK: {d}")
    
    if all_ok:
        print("\nSetup successful. Ready for data ingestion.")
        sys.exit(0)
    else:
        print("\nSetup failed. Check directory permissions.")
        sys.exit(1)

if __name__ == "__main__":
    main()