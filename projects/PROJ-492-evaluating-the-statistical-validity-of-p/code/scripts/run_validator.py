"""
Script to run the inconsistency validator on reconstructed summaries.
Reads from data/reconstructed_summaries.json and writes to output/audit_report.json.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.src.audit.validator import main as validator_main


def main():
    """Entry point for validator script."""
    try:
        validator_main()
    except Exception as e:
        print(f"Error running validator: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
