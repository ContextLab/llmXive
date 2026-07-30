"""
CLI script to run metadata verification.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.data.verify_metadata import main

if __name__ == "__main__":
    main()
