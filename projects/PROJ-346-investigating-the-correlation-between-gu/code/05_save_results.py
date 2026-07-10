"""
Task T026: Save correlation matrix and regression results to data/processed/ with metadata.

This script aggregates outputs from T021 (Correlation) and T023 (Regression),
attaches execution metadata, and saves them as Parquet files in the processed directory.
It handles the case where the merged dataset is missing (Data Gap) by generating
a "Not Measurable" artifact as per FR-008 and SC-001/SC-004.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

# Add project root to path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent))

from utils import (
    get_project_root_path,
    get_data_processed_path,
    get_logger,
    write_json_log,
    ensure_directory
)
from config import load_dataset_urls

# Configure logging
logger = get_logger(__name__)

def load_correlation_results() -> pd.DataFrame:
    """Load correlation results from the previous step."""
    processed_dir = get_data_processed_path()
    corr_file = processed_dir / "correlation_results.parquet"
    
    if not corr_file.exists():
        logger.warning(f"Correlation results file not found at {corr_file}. Returning empty DataFrame.")
        return pd.DataFrame()
    
    try:
        return pd.read_parquet(corr_file)
    except Exception as e:
        logger.error(f"Failed to load correlation results: {e}")
        return pd.DataFrame()

def load_regression_results() -> pd.DataFrame:
    """Load regression results from the previous step."""
    processed_dir = get_data_processed_path()
    reg_file = processed_dir / "regression_results.parquet"
    
    if not reg_file.exists():
        logger.warning(f"Regression results file not found at {reg_file}. Returning empty DataFrame.")
        return pd.DataFrame()
    
    try:
        return pd.read_parquet(reg_file)
    except Exception as e:
        logger.error(f"Failed to load regression results: {e}")
        return pd.DataFrame()

def create_metadata(status: str, source_files: list, notes: str = "") -> dict:
    """Generate execution metadata."""
    return {
        "task_id": "T026",
        "task_description": "Save correlation matrix and regression results with metadata",
        "execution_timestamp": datetime.utcnow().isoformat(),
        "status": status,
        "source_files": source_files,
        "notes": notes,
        "version": "1.0.0"
    }

def save_with_metadata(df: pd.DataFrame, filename: str, metadata: dict, is_empty: bool = False):
    """Save a DataFrame to parquet with an accompanying JSON metadata file."""
    processed_dir = get_data_processed_path()
    ensure_directory(processed_dir)
    
    output_path = processed_dir / filename
    meta_path = processed_dir / f"{filename}.meta.json"
    
    if is_empty or df.empty:
        # Save empty dataframe with metadata indicating N/A
        df.to_parquet(output_path, index=False)
        metadata["data_status"] = "N/A - Data Gap or No Results"
        logger.info(f"Saved empty results to {output_path} with N/A metadata.")
    else:
        df.to_parquet(output_path, index=False)
        metadata["data_status"] = "Complete"
        metadata["row_count"] = len(df)
        logger.info(f"Saved {len(df)} rows to {output_path}.")
    
    with open(meta_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return output_path, meta_path

def main():
    logger.info("Starting T026: Saving correlation and regression results.")
    
    processed_dir = get_data_processed_path()
    merged_file = processed_dir / "merged_dataset.parquet"
    
    # Check for Data Gap condition
    if not merged_file.exists():
        logger.warning("Merged dataset not found. Data Gap detected. Generating N/A artifacts.")
        
        # Create empty result sets
        empty_corr = pd.DataFrame(columns=["taxon", "cognitive_metric", "correlation", "p_value", "q_value", "significant"])
        empty_reg = pd.DataFrame(columns=["feature", "coefficient", "standard_error", "p_value", "selected"])
        
        meta = create_metadata(
            status="N/A",
            source_files=[],
            notes="Data Gap: Merged dataset (merged_dataset.parquet) not found. Per FR-008, results are Not Measurable."
        )
        
        save_with_metadata(empty_corr, "correlation_results.parquet", meta, is_empty=True)
        save_with_metadata(empty_reg, "regression_results.parquet", meta, is_empty=True)
        
        logger.info("T026 completed with N/A status due to data gap.")
        return

    # Load existing results
    corr_df = load_correlation_results()
    reg_df = load_regression_results()
    
    source_files = []
    if not corr_df.empty:
        source_files.append("correlation_results.parquet")
    if not reg_df.empty:
        source_files.append("regression_results.parquet")
    
    # Create metadata
    meta = create_metadata(
        status="Success",
        source_files=source_files,
        notes="Correlation and regression results aggregated and saved with metadata."
    )
    
    # Save Correlation Results
    if not corr_df.empty:
        save_with_metadata(corr_df, "correlation_results.parquet", meta, is_empty=False)
    else:
        # Even if empty, save with metadata if merged data exists but no correlations found
        save_with_metadata(corr_df, "correlation_results.parquet", meta, is_empty=True)

    # Save Regression Results
    if not reg_df.empty:
        save_with_metadata(reg_df, "regression_results.parquet", meta, is_empty=False)
    else:
        save_with_metadata(reg_df, "regression_results.parquet", meta, is_empty=True)
    
    logger.info("T026 completed successfully.")

if __name__ == "__main__":
    main()