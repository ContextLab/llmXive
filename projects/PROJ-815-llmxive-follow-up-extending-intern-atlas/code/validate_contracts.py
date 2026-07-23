"""
Script to validate the extracted dataset against the project contracts.
Implements Task T017b.
"""
import os
import sys
from pathlib import Path

# Ensure code directory is in path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from utils.schema_validator import validate_dataset

# Paths defined in tasks.md and spec
PROJECT_ROOT = current_dir.parent
DATA_FILE = PROJECT_ROOT / "data" / "processed" / "features_2010_2018.csv"
SCHEMA_FILE = PROJECT_ROOT / "specs" / "001-llmxive-follow-up-extending-intern-atlas" / "contracts" / "dataset.schema.yaml"

def main():
    print(f"Starting contract validation for task T017b...")
    print(f"Dataset: {DATA_FILE}")
    print(f"Schema: {SCHEMA_FILE}")

    if not DATA_FILE.exists():
        print(f"ERROR: Dataset file not found at {DATA_FILE}")
        print("Aborting: No ground truth labels or data found for validation.")
        sys.exit(1)

    if not SCHEMA_FILE.exists():
        print(f"ERROR: Schema file not found at {SCHEMA_FILE}")
        sys.exit(1)

    # Run validation
    is_valid, errors = validate_dataset(str(DATA_FILE), str(SCHEMA_FILE))

    if not is_valid:
        print("\n❌ VALIDATION FAILED")
        print("The dataset does not conform to the required contract.")
        print("Errors found:")
        for err in errors:
            print(f"  - {err}")
        print("\nAborting: Validation failed.")
        sys.exit(1)
    else:
        print("\n✅ VALIDATION PASSED")
        print("Dataset conforms to the contract in dataset.schema.yaml")
        sys.exit(0)

if __name__ == "__main__":
    main()
