"""
CLI Script to verify state integrity.

This script serves as the entry point for the T038 task,
allowing users to run the verification logic from the command line.

Usage:
    python code/scripts/verify_state_cli.py
    python code/scripts/verify_state_cli.py --state-dir /custom/path
    python code/scripts/verify_state_cli.py --update
"""
import sys
from pathlib import Path

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from state_manager import main

if __name__ == "__main__":
    sys.exit(main())