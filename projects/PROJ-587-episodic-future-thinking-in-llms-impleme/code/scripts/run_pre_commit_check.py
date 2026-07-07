"""
Script to run the pre-commit validation manually.
This simulates the pre-commit hook for testing purposes.
"""

import sys
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent
sys.path.insert(0, str(code_dir))

from utils.reference_validator import pre_commit_hook

if __name__ == "__main__":
    exit_code = pre_commit_hook()
    sys.exit(exit_code)