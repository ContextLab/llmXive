"""
code/verify_research_cli.py

Entry point for Task T013 verification.
This script is intended to be run to verify the research file before proceeding.
"""

import sys
from pathlib import Path

# Ensure the code directory is in the path
code_dir = Path(__file__).parent
sys.path.insert(0, str(code_dir))

from verify_research import verify_research_file

def main():
    """
    Main entry point for the verification script.
    """
    print("Starting Research File Verification (Task T013)...")
    try:
        verify_research_file()
        print("Verification PASSED.")
        return 0
    except Exception as e:
        print(f"Verification FAILED: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())