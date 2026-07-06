"""
Script to run the validator on test data and generate the audit report.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.src.audit.validator import main as validator_main

if __name__ == "__main__":
    # Run validator with test data
    sys.argv = [
        "run_validator.py",
        "--input", str(project_root / "data" / "validator_test_summaries.json"),
        "--output", str(project_root / "output" / "audit_report.json")
    ]
    exit_code = validator_main()
    sys.exit(exit_code)