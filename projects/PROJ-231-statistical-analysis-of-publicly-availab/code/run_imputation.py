"""
Script to execute the spline-based imputation (T013) on the downloaded CMIP6 data.

This script:
1. Downloads the real CMIP6 dataset (streaming).
2. Applies the spline imputation logic.
3. Saves the processed data to data/processed/imputed_cmip6.parquet.
"""
import os
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion import download_cmip6_data, apply_imputation_to_dataset
from config import get_data_dir
from logging_config import setup_logging

def main():
    # Setup logging
    setup_logging(level="INFO")

    data_dir = get_data_dir()
    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    output_file = processed_dir / "imputed_cmip6.parquet"

    print(f"Starting T013 Imputation Pipeline. Output: {output_file}")

    # 1. Download Data
    try:
        dataset = download_cmip6_data(streaming=True)
    except Exception as e:
        print(f"CRITICAL: Failed to download data. Aborting. Error: {e}")
        sys.exit(1)

    # 2. Apply Imputation
    # Note: For a real large dataset, this loop might need to be chunked.
    # We assume the dataset is iterable.
    try:
        processed_data = apply_imputation_to_dataset(dataset)
    except Exception as e:
        print(f"CRITICAL: Imputation process failed. Error: {e}")
        sys.exit(1)

    # 3. Save Output
    try:
        import pandas as pd
        df = pd.DataFrame(processed_data)
        df.to_parquet(output_file, index=False)
        print(f"SUCCESS: Processed data saved to {output_file}")
        print(f"Total rows processed: {len(df)}")
    except ImportError:
        print("WARNING: pandas and pyarrow not installed. Saving as JSON instead.")
        json_file = str(output_file).replace('.parquet', '.json')
        with open(json_file, 'w') as f:
            # Convert numpy arrays to lists for JSON serialization
            json.dump([
                {k: (v.tolist() if hasattr(v, 'tolist') else v) for k, v in row.items()}
                for row in processed_data
            ], f, indent=2)
        print(f"SUCCESS: Processed data saved to {json_file}")
    except Exception as e:
        print(f"CRITICAL: Failed to save output. Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
