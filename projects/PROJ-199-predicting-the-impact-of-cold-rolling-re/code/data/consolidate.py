"""
Consolidate preprocessed EBSD data into a single Parquet file.

This module implements Task T015: Generate consolidated Parquet output to
`data/processed/cleaned_ebsd.parquet` with metadata (material, reduction, confidence).

Logic:
1. Load all processed datasets from the `data/interim` directory (output of T014).
2. Concatenate into a single DataFrame.
3. Validate that at least one row exists. If zero valid rows, raise an error.
4. Write to `data/processed/cleaned_ebsd.parquet`.
5. Log a summary of excluded/missing entries.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import pandas as pd

# Import logging utility from the project's utils
from utils.logging import get_logger

# Ensure the code directory is in the path for imports if running as script
# This is handled by the project structure, but good practice for scripts
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logger = get_logger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
INTERIM_DIR = PROJECT_ROOT / "data" / "interim"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = PROCESSED_DIR / "cleaned_ebsd.parquet"

def load_all_processed_datasets() -> pd.DataFrame:
    """
    Load all parquet files from the interim directory and concatenate them.

    Returns:
        pd.DataFrame: Concatenated dataframe of all processed EBSD data.

    Raises:
        FileNotFoundError: If no parquet files are found in the interim directory.
        ValueError: If the combined dataset is empty.
    """
    if not INTERIM_DIR.exists():
        logger.error(f"Interim directory not found: {INTERIM_DIR}")
        raise FileNotFoundError(f"Interim directory not found: {INTERIM_DIR}")

    parquet_files = list(INTERIM_DIR.glob("*.parquet"))
    
    if not parquet_files:
        logger.error(f"No parquet files found in {INTERIM_DIR}. "
                     "Did T014 (preprocess) run successfully?")
        raise FileNotFoundError(f"No parquet files found in {INTERIM_DIR}. "
                                "Did T014 (preprocess) run successfully?")

    logger.info(f"Found {len(parquet_files)} parquet files in {INTERIM_DIR}")

    dataframes = []
    for file_path in parquet_files:
        try:
            df = pd.read_parquet(file_path)
            logger.debug(f"Loaded {file_path.name}: {len(df)} rows")
            
            # Ensure required columns exist (metadata from T014)
            required_cols = ['material', 'reduction', 'confidence']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                logger.warning(f"File {file_path.name} missing columns: {missing_cols}. "
                               "Skipping file.")
                continue
            
            dataframes.append(df)
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            continue

    if not dataframes:
        logger.error("No valid dataframes could be loaded from the interim directory.")
        raise ValueError("No valid dataframes could be loaded from the interim directory.")

    combined_df = pd.concat(dataframes, ignore_index=True)
    logger.info(f"Combined dataset has {len(combined_df)} rows across {len(dataframes)} files.")
    
    return combined_df

def write_consolidated_parquet(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """
    Write the consolidated dataframe to a Parquet file.

    Args:
        df: The consolidated DataFrame.
        output_path: Optional path to write to. Defaults to data/processed/cleaned_ebsd.parquet.

    Returns:
        Path: The path of the written file.

    Raises:
        ValueError: If the input DataFrame is empty.
    """
    if output_path is None:
        output_path = OUTPUT_FILE

    if df.empty:
        error_msg = "Cannot write empty dataset. Input DataFrame has zero rows."
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to Parquet
    df.to_parquet(output_path, index=False)
    logger.info(f"Successfully wrote consolidated data to {output_path} ({len(df)} rows).")

    # Log summary of materials and reductions
    materials = df['material'].unique().tolist()
    reductions = sorted(df['reduction'].unique().tolist())
    logger.info(f"Materials in output: {materials}")
    logger.info(f"Reductions in output: {reductions}")

    return output_path

def main():
    """Main entry point for the consolidation script."""
    logger.info("Starting EBSD data consolidation (Task T015)...")
    
    try:
        # Step 1: Load all processed datasets
        logger.info("Loading processed datasets from interim directory...")
        combined_df = load_all_processed_datasets()

        # Step 2: Validate data exists (T015 Zero-Data Handling)
        if combined_df.empty:
            logger.error("Consolidation failed: No valid data found after loading.")
            logger.error("Task T015 requires at least one valid row to generate output.")
            sys.exit(1)

        # Step 3: Write consolidated Parquet
        logger.info("Writing consolidated Parquet file...")
        output_path = write_consolidated_parquet(combined_df)

        # Step 4: Log summary
        logger.info("Consolidation complete.")
        logger.info(f"Output file: {output_path}")
        
        # Summary statistics
        total_rows = len(combined_df)
        excluded_samples = 0 # This would be tracked if we had input counts, but we assume T014 did exclusion
        logger.info(f"Total valid rows in final output: {total_rows}")
        
        return 0

    except FileNotFoundError as e:
        logger.error(f"Data source error: {e}")
        logger.error("Task T015 cannot proceed without input from T014.")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        logger.error("Task T015 failed: Zero valid rows found.")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during consolidation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
