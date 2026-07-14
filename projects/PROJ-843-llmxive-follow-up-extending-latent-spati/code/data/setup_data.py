import sys
from pathlib import Path
import json
from config import (
    get_data_dir,
    get_raw_dir,
    get_processed_dir,
    get_stratified_dir,
    get_features_dir,
    get_results_dir
)
from data.schemas import (
    create_directories,
    validate_strata_existence,
    create_schema_report
)
from utils.seeds import set_global_seed

def main():
    """
    Entry point for initial data setup.
    Creates directory structure and validates schema compliance.
    """
    print("Starting data setup...")
    
    # Set seed for reproducibility
    set_global_seed(42)
    
    # Create directories
    print("Creating directory structure...")
    dirs = create_directories()
    
    success = True
    for path, status in dirs.items():
        if status:
            print(f"  [OK] {path}")
        else:
            print(f"  [FAIL] {path}")
            success = False
    
    if not success:
        print("Error: Failed to create some directories.")
        return 1
    
    # Validate schema
    print("\nValidating schema compliance...")
    report = create_schema_report()
    
    if report['status'] == 'valid':
        print("Schema validation passed.")
    else:
        print("Schema validation failed. Missing strata may need to be populated by downstream tasks.")
        # This is not a fatal error for setup, as strata are created by stratify.py
    
    print("\nData setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
