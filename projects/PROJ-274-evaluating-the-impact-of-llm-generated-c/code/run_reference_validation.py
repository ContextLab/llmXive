"""
Runner script for the Reference Validator Agent (Task T071b).
Executes validation against the research document and creates the validation lock.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from utils.validator import main

if __name__ == "__main__":
    sys.exit(main())