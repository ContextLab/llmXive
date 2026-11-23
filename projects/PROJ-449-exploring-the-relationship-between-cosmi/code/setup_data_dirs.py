"""
Setup script to create the required directory structure for the project.
"""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.data import ensure_data_structure, RAW_DIR, PROCESSED_DIR, CHECKSUMS_FILE

def main():
    """Create the required directory structure."""
    ensure_data_structure()
    print(f"Data directories created:")
    print(f"  - {RAW_DIR}")
    print(f"  - {PROCESSED_DIR}")
    print(f"  - {CHECKSUMS_FILE}")

if __name__ == "__main__":
    main()