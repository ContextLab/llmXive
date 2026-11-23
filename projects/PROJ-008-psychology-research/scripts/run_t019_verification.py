"""
Script to run T019 verification.
This script executes the verification logic defined in code/data/verify_output.py
to ensure that the pipeline (T014-T018) has successfully generated the required
artifacts: data/processed/cleaned_studies.csv and data/raw/excluded_studies.log.
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.data.verify_output import main

if __name__ == "__main__":
    print("Running T019 Verification Script...")
    print("=" * 60)
    success = main()
    print("=" * 60)
    if success:
        print("T019 Verification completed successfully.")
        sys.exit(0)
    else:
        print("T019 Verification failed.")
        sys.exit(1)