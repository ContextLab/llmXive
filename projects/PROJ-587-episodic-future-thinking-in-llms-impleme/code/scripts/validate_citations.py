"""
Script to run citation validation as a pre-commit hook or standalone command.

This script serves as the entry point for the pre-commit hook configured
in .pre-commit-config.yaml and can also be run manually.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.reference_validator import pre_commit_hook

def main():
    """Run the pre-commit hook validation."""
    exit_code = pre_commit_hook()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()