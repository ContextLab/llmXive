"""
Script to run the Defense Allocation Index calculation (T039).
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.analysis.defense_index import main

if __name__ == "__main__":
    sys.exit(main())
