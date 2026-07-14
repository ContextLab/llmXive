import sys
from pathlib import Path
from config import get_raw_dir, get_stratified_dir, get_features_dir, get_results_dir
from data.schemas import create_directories, ensure_schema_compliance

def main():
    """Initialize data directories and schema."""
    print("Setting up data directories...")
    create_directories()
    ensure_schema_compliance()
    print("Data setup complete.")

if __name__ == "__main__":
    main()