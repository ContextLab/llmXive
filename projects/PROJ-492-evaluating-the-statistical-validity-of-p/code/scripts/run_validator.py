"""
Script to run the validator on reconstructed summaries.

Reads from data/reconstructed_summaries.json and writes to output/audit_report.json.
"""

import sys
from pathlib import Path

from code.src.audit.validator import main as validator_main

def main():
    """Entry point for the validator script."""
    try:
        validator_main()
    except Exception as e:
        print(f"Error running validator: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()