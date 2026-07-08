"""
Script to run the inconsistency validator on sample data.
Usage: python scripts/run_validator.py
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.src.audit.validator import main as validator_main

if __name__ == "__main__":
    # Default paths
    input_path = project_root / "data" / "sample_summaries_for_validation.json"
    output_path = project_root / "output" / "audit_report.json"

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    # Override sys.argv to pass arguments
    sys.argv = ["run_validator.py", "--input", str(input_path), "--output", str(output_path)]
    validator_main()
    print(f"Audit report written to: {output_path}")