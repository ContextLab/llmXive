"""
Runner script for T018: Write Harmonized Dataset.
This script orchestrates the pipeline to generate, validate, harmonize, and write the dataset.
It assumes T013-T016 logic is encapsulated in ingestion.py.
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import get_config, get_project_root
from ingestion import validate_dgp_config, run_dgp_pipeline

def main():
    print("Starting T018: Write Harmonized Dataset")
    print("========================================")
    
    # Load configuration
    config = get_config()
    project_root = get_project_root()
    
    # Ensure directories exist
    raw_dir = project_root / 'data' / 'raw'
    processed_dir = project_root / 'data' / 'processed'
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Validate DGP config
    validate_dgp_config(config['dgp'])
    
    # Run the full pipeline (includes generation, validation, harmonization, fitting, and writing)
    # Note: run_dgp_pipeline handles T014, T014b, T015a, T015c, T016, and T018 internally.
    # It writes to data/raw for intermediate CSVs and data/processed for the final parquet.
    try:
        final_df = run_dgp_pipeline(config['dgp'], raw_dir)
        print("Pipeline completed successfully.")
        print(f"Final dataset shape: {final_df.shape}")
        print(f"Columns: {list(final_df.columns)}")
    except SystemExit as e:
        if e.code != 0:
            print(f"Pipeline failed with exit code {e.code}")
            sys.exit(e.code)
    
    print("T018 Complete.")

if __name__ == '__main__':
    main()