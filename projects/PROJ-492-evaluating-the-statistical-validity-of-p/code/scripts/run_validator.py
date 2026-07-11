"""
Script to run the inconsistency validator (T025) on project data.
"""

import sys
from pathlib import Path

# Add project root to path if necessary
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.src.audit.validator import main

if __name__ == "__main__":
    main()
