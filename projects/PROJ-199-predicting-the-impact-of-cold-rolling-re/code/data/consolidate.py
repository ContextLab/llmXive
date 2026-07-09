"""
Consolidate preprocessed EBSD data into a single Parquet file with metadata.

This script reads the processed EBSD data (output of T012), applies exclusion logic
(T014), and generates the final `data/processed/cleaned_ebsd.parquet` artifact
required for downstream analysis (US2).
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

import pandas as pd
import numpy as np

# Project imports
from utils.logging import get_logger, configure_lineage
from data.preprocess import process_ebsd_dataset, load_ebsd_data, filter_by_confidence, reindex_to_fcc
from data.exclusion import calculate_reliability_metrics, apply_exclusion_logic
from config import get_reductions, get_seed, ConfigurationError

# Setup logging
logger = get_logger(__name__)
configure_lineage(__file__)

def load_all_processed_datasets(base_dir: Path) -> List[pd.DataFrame]:
    """
    Load all processed EBSD datasets from the interim/processed directory.
    Expects files named like 'processed_<material>_<reduction>.csv' or similar
    as produced by T012.
    """
    processed_dir = base_dir / "interim"
    if not processed_dir.exists():
        raise FileNotFoundError(f"Processed directory not found: {processed_dir}")

    dfs = []
    for file_path in processed_dir.glob("*.csv"):
        logger.info(f"Loading processed file: {file_path}")
        try:
            df = pd.read_csv(file_path)
            # Ensure required columns exist
            required_cols = ['sample_id', 'material', 'reduction', 'confidence', 'phi1', 'Phi', 'phi2']
            if not all(col in df.columns for col in required_cols):
                logger.warning(f"Skipping {file_path}: missing required columns. Found: {df.columns.tolist()}")
                continue
            dfs.append(df)
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
    
    if not dfs:
        raise RuntimeError("No valid processed datasets found in interim directory.")
    
    return dfs

def main():
    """Main entry point for T015."""
    # Paths
    project_root = Path(__file__).resolve().parent.parent.parent
    output_dir = project_root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "cleaned_ebsd.parquet"

    logger.info(f"Starting consolidation to {output_file}")

    try:
        # 1. Load all processed datasets
        all_dfs = load_all_processed_datasets(project_root)
        combined_df = pd.concat(all_dfs, ignore_index=True)
        logger.info(f"Combined {len(combined_df)} rows from {len(all_dfs)} files.")

        # 2. Apply Exclusion Logic (T014)
        # Calculate reliability metrics per sample
        reliability_df = calculate_reliability_metrics(combined_df)
        
        # Apply exclusion logic to get list of valid sample IDs
        valid_sample_ids = apply_exclusion_logic(reliability_df)
        
        # Filter the main dataframe
        initial_count = len(combined_df)
        filtered_df = combined_df[combined_df['sample_id'].isin(valid_sample_ids)]
        final_count = len(filtered_df)
        excluded_count = initial_count - final_count
        
        logger.info(f"Exclusion applied: {excluded_count} rows removed ({excluded_count/initial_count*100:.2f}%).")
        logger.info(f"Remaining valid samples: {len(valid_sample_ids)}")

        # 3. Add Metadata Columns
        # Ensure 'material' and 'reduction' are strings for Parquet consistency
        filtered_df['material'] = filtered_df['material'].astype(str)
        filtered_df['reduction'] = filtered_df['reduction'].astype(str)
        
        # Add a timestamp for lineage
        filtered_df['processed_at'] = pd.Timestamp.now()

        # 4. Save to Parquet
        # Using pyarrow engine for better compression and metadata support
        filtered_df.to_parquet(
            output_file, 
            engine='pyarrow', 
            index=False,
            compression='snappy'
        )

        logger.info(f"Successfully wrote {output_file}")
        logger.info(f"Final schema: {filtered_df.dtypes.to_dict()}")
        
        # Print summary stats
        logger.info("Summary Statistics:")
        logger.info(f"  Total Rows: {final_count}")
        logger.info(f"  Unique Materials: {filtered_df['material'].nunique()}")
        logger.info(f"  Unique Reductions: {filtered_df['reduction'].nunique()}")
        
    except ConfigurationError as ce:
        logger.error(f"Configuration error: {ce}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during consolidation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()