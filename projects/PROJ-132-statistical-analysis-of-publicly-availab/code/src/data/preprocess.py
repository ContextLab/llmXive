import os
import sys
import hashlib
import yaml
import logging
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

from src.config import setup_logging

# Ensure the logger is configured for this module
logger = logging.getLogger(__name__)

def mark_insufficient_cells(
    df: pd.DataFrame,
    min_count: int = 5,
    output_path: Optional[Path] = None,
    log_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Scan aggregated grid cells and mark those with insufficient data.

    Logic:
    1. Scan aggregated grid cells.
    2. If count < min_count (default 5), set data_quality="insufficient".
    3. Exclude these cells from downstream modeling by filtering them out
       (or flagging them, depending on downstream needs).
    4. Log species, grid cell, and reason to the provided log path.
    5. Write metadata to data/processed/metadata_insufficient_cells.json.

    Args:
        df: DataFrame containing aggregated grid cell data.
            Expected columns: 'species', 'grid_cell', 'count', and others.
        min_count: Minimum count threshold for sufficient data.
        output_path: Optional path to write the metadata JSON.
        log_path: Optional path to the pipeline log file.

    Returns:
        DataFrame with a new column 'data_quality' where insufficient cells
        are marked as "insufficient".
    """
    if df.empty:
        logger.warning("Input DataFrame is empty. No cells to mark.")
        return df

    # Ensure 'count' column exists
    if 'count' not in df.columns:
        raise ValueError("Input DataFrame must contain a 'count' column.")

    # Initialize data_quality column
    df['data_quality'] = 'sufficient'

    # Identify insufficient cells
    insufficient_mask = df['count'] < min_count
    insufficient_df = df[insufficient_mask]

    if not insufficient_df.empty:
        # Update data_quality for insufficient cells
        df.loc[insufficient_mask, 'data_quality'] = 'insufficient'

        # Prepare metadata for insufficient cells
        insufficient_metadata = insufficient_df[['species', 'grid_cell', 'count']].to_dict(
            orient='records'
        )

        # Add reason to metadata
        for record in insufficient_metadata:
            record['reason'] = f"Count ({record['count']}) is below threshold ({min_count})."
            record['timestamp'] = datetime.now(timezone.utc).isoformat()

        # Log insufficient cells
        if log_path:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, 'a', encoding='utf-8') as log_file:
                for record in insufficient_metadata:
                    log_entry = (
                        f"[INSUFFICIENT] species={record['species']}, "
                        f"grid_cell={record['grid_cell']}, "
                        f"count={record['count']}, "
                        f"reason={record['reason']}\n"
                    )
                    log_file.write(log_entry)
            logger.info(f"Logged {len(insufficient_metadata)} insufficient cells to {log_path}.")

        # Write metadata to output path
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as meta_file:
                json.dump(insufficient_metadata, meta_file, indent=2)
            logger.info(f"Wrote insufficient cells metadata to {output_path}.")
        else:
            logger.warning("No output path provided for insufficient cells metadata.")

    else:
        logger.info("No insufficient cells found.")

    return df

def run_preprocessing_pipeline(
    input_path: Path,
    output_path: Path,
    log_path: Optional[Path] = None,
    metadata_path: Optional[Path] = None,
    min_count: int = 5
) -> None:
    """
    Run the full preprocessing pipeline including marking insufficient cells.

    This function:
    1. Loads the aggregated data from input_path.
    2. Calls mark_insufficient_cells to flag cells with insufficient data.
    3. Writes the processed DataFrame to output_path.
    4. Logs and writes metadata for insufficient cells.

    Args:
        input_path: Path to the input aggregated data (e.g., parquet or csv).
        output_path: Path to write the processed DataFrame.
        log_path: Path to the pipeline log file.
        metadata_path: Path to write the insufficient cells metadata JSON.
        min_count: Minimum count threshold for sufficient data.
    """
    logger.info(f"Starting preprocessing pipeline. Input: {input_path}, Output: {output_path}")

    # Load data
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if input_path.suffix == '.parquet':
        df = pd.read_parquet(input_path)
    elif input_path.suffix == '.csv':
        df = pd.read_csv(input_path)
    else:
        raise ValueError(f"Unsupported file format: {input_path.suffix}")

    logger.info(f"Loaded {len(df)} records from {input_path}")

    # Mark insufficient cells
    df_processed = mark_insufficient_cells(
        df=df,
        min_count=min_count,
        output_path=metadata_path,
        log_path=log_path
    )

    # Filter out insufficient cells for downstream modeling (optional, depending on needs)
    # Here we keep all rows but mark them; downstream can filter if needed.
    # If we want to exclude them:
    # df_processed = df_processed[df_processed['data_quality'] != 'insufficient']

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix == '.parquet':
        df_processed.to_parquet(output_path, index=False)
    elif output_path.suffix == '.csv':
        df_processed.to_csv(output_path, index=False)
    else:
        raise ValueError(f"Unsupported output format: {output_path.suffix}")

    logger.info(f"Preprocessing pipeline completed. Output written to {output_path}")

def main() -> None:
    """
    Main entry point for the preprocessing pipeline.

    This function:
    1. Sets up logging.
    2. Defines input and output paths.
    3. Runs the preprocessing pipeline.
    """
    # Set up logging
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "pipeline.log"

    # Configure logging
    logger = setup_logging(log_file=log_path)

    # Define paths
    input_path = Path("data/interim/aggregated_data.parquet")
    output_path = Path("data/processed/processed_data.parquet")
    metadata_path = Path("data/processed/metadata_insufficient_cells.json")

    # Run pipeline
    try:
        run_preprocessing_pipeline(
            input_path=input_path,
            output_path=output_path,
            log_path=log_path,
            metadata_path=metadata_path,
            min_count=5
        )
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()