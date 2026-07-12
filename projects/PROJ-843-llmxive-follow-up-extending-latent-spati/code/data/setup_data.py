"""
Setup script for initializing the data directory structure.
This script should be run once to create the base data directories.
"""
import sys
from pathlib import Path

from config import (
    get_data_dir,
    get_raw_dir,
    get_processed_dir,
    get_stratified_dir,
    get_features_dir,
    get_results_dir,
    ensure_directories
)
from data.schemas import (
    create_directories,
    validate_directory_structure,
    validate_strata_existence,
    create_schema_report
)

def main():
    """
    Main entry point for data setup.
    Creates all required directories and generates a schema report.
    """
    print("Initializing data directory structure...")
    
    # Create all directories
    success = create_directories()
    if not success:
        print("ERROR: Failed to create directory structure.")
        sys.exit(1)
        
    print("Directories created successfully.")
    
    # Validate structure
    is_valid, missing = validate_directory_structure()
    if not is_valid:
        print(f"WARNING: Some directories are missing: {missing}")
        # We already created them, so this shouldn't happen
    else:
        print("Directory structure validated successfully.")
        
    # Create schema report
    report_path = create_schema_report()
    print(f"Schema report generated at: {report_path}")
    
    # Print summary
    print("\nData directory structure:")
    print(f"  - {get_data_dir()}")
    print(f"  - {get_raw_dir()}")
    print(f"  - {get_processed_dir()}")
    print(f"  - {get_stratified_dir()}")
    print(f"  - {get_features_dir()}")
    print(f"  - {get_results_dir()}")
    
    print("\nSetup complete.")

if __name__ == "__main__":
    main()