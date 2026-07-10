"""
Script to explicitly initialize the data directory structure.
This serves as the executable entry point for T006.
"""
import sys
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from code.data import ensure_data_structure, RAW_DIR, PROCESSED_DIR, CHECKSUMS_FILE

def main():
    print("Initializing data directory structure...")
    ensure_data_structure()
    
    print(f"Created: {RAW_DIR}")
    print(f"Created: {PROCESSED_DIR}")
    print(f"Created: {CHECKSUMS_FILE}")
    
    # Verify creation
    if RAW_DIR.exists() and PROCESSED_DIR.exists() and CHECKSUMS_FILE.exists():
        print("SUCCESS: Data structure initialized correctly.")
        return 0
    else:
        print("ERROR: Failed to create all required directories/files.")
        return 1

if __name__ == "__main__":
    sys.exit(main())