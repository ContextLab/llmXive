import sys
from pathlib import Path
import json

from config import (
    get_data_dir,
    get_results_dir
)
from data.schemas import (
    create_directories,
    validate_directory_structure,
    create_schema_report,
    ensure_schema_compliance
)
from utils.seeds import set_global_seed


def main():
    """
    Main entry point to initialize the data directory structure and validate schema.
    This script is intended to be run once at the start of the pipeline to ensure
    the environment is ready.
    """
    print("Initializing data directory structure...")
    set_global_seed(42)

    # Ensure all directories exist
    paths = create_directories()
    
    print(f"Data root: {get_data_dir()}")
    print(f"Raw: {paths['raw']}")
    print(f"Stratified: {paths['stratified']}")
    print(f"Features: {paths['features']}")
    print(f"Results: {paths['results']}")

    # Validate structure
    is_valid, missing = validate_directory_structure()
    if not is_valid:
        print(f"ERROR: Directory structure validation failed. Missing: {missing}")
        sys.exit(1)
    
    print("Directory structure validation: PASSED")

    # Generate schema report
    report_path = get_results_dir() / "schema_report.json"
    create_schema_report(report_path)
    print(f"Schema report written to: {report_path}")

    print("Data setup complete.")


if __name__ == "__main__":
    main()