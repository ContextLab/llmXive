"""
Helper script to run T014 preprocessing.
This ensures the script can be invoked directly if needed,
though the main logic is in preprocess.py.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ingest.preprocess import main

if __name__ == "__main__":
    main()