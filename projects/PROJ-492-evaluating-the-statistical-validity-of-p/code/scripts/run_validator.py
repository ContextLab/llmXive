"""
Script to run the validator on processed data.
"""
import sys
from pathlib import Path

# Add project root to path if running as script
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.src.audit.validator import main

if __name__ == "__main__":
    sys.exit(main())