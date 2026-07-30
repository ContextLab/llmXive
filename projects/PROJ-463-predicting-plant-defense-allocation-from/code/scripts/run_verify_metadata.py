import sys
from pathlib import Path

# Add project root to path if not already present
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.verify_metadata import main

def main():
    """CLI wrapper for metadata verification."""
    return main()

if __name__ == "__main__":
    main()