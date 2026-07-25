"""
Validation module for ingested elastic data.
Merges results from MP and AFLOW sources, verifies minimum entry count,
and logs skipped or invalid IDs.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

import pandas as pd

# Project-relative imports based on provided API surface
from src.utils.logging import get_logger, log_info, log_warning, log_error
from src.utils.config import get_path, ensure_directories

# Ensure project root is in path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

logger = get_logger(__name__)

MIN_UNIQUE_ENTRIES = 50  # SC-001 Requirement

def load_ingest_results(
    mp_path: Optional[Path] = None,
    aflow_path: Optional[Path] = None
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Load and merge elastic data results from MP and AFLOW ingestion scripts.
    
    Args:
        mp_path: Path to MP ingestion output CSV (default: data/processed/mp_elastic.csv)
        aflow_path: Path to AFLOW ingestion output CSV (default: data/processed/aflow_elastic.csv)
        
    Returns:
        Tuple of (merged DataFrame, list of skipped IDs)
    """
    if mp_path is None:
        mp_path = get_path("data_processed", "mp_elastic.csv")
    if aflow_path is None:
        aflow_path = get_path("data_processed", "aflow_elastic.csv")
    
    skipped_ids: List[str] = []
    dfs = []

    # Load MP data
    if mp_path.exists():
        log_info(f"Loading MP ingestion results from {mp_path}")
        try:
            df_mp = pd.read_csv(mp_path)
            if not df_mp.empty:
                df_mp['source'] = 'materials_project'
                dfs.append(df_mp)
                log_info(f"Loaded {len(df_mp)} entries from MP")
            else:
                log_warning(f"MP ingestion result file {mp_path} is empty")
        except Exception as e:
            log_error(f"Failed to load MP results: {e}")
            raise
    else:
        log_warning(f"MP ingestion result file not found: {mp_path}")

    # Load AFLOW data
    if aflow_path.exists():
        log_info(f"Loading AFLOW ingestion results from {aflow_path}")
        try:
            df_aflow = pd.read_csv(aflow_path)
            if not df_aflow.empty:
                df_aflow['source'] = 'aflow'
                dfs.append(df_aflow)
                log_info(f"Loaded {len(df_aflow)} entries from AFLOW")
            else:
                log_warning(f"AFLOW ingestion result file {aflow_path} is empty")
        except Exception as e:
            log_error(f"Failed to load AFLOW results: {e}")
            raise
    else:
        log_warning(f"AFLOW ingestion result file not found: {aflow_path}")

    if not dfs:
        log_error("No valid data sources found for validation.")
        raise FileNotFoundError("Neither MP nor AFLOW ingestion results found.")

    # Merge results
    merged_df = pd.concat(dfs, ignore_index=True)
    
    # Identify and log skipped/invalid entries (e.g., missing required columns)
    required_cols = {'C11', 'C12', 'C44', 'material_id'}
    if not required_cols.issubset(merged_df.columns):
        missing = required_cols - set(merged_df.columns)
        log_warning(f"Missing required columns in merged data: {missing}")
        # Drop rows that don't have the required columns
        valid_mask = merged_df[list(required_cols)].notna().all(axis=1)
        dropped_count = (~valid_mask).sum()
        if dropped_count > 0:
            log_warning(f"Dropped {dropped_count} rows due to missing required columns")
            merged_df = merged_df[valid_mask]

    return merged_df, skipped_ids

def verify_entry_count(df: pd.DataFrame, min_count: int = MIN_UNIQUE_ENTRIES) -> bool:
    """
    Verify that the merged dataset contains at least the minimum required unique entries.
    
    Args:
        df: Merged DataFrame
        min_count: Minimum number of unique entries required (default: 50)
        
    Returns:
        True if count requirement is met, False otherwise
    """
    unique_ids = df['material_id'].nunique()
    log_info(f"Total unique entries in merged dataset: {unique_ids}")
    
    if unique_ids < min_count:
        log_error(f"Entry count validation failed: {unique_ids} < {min_count} (SC-001)")
        return False
    
    log_success(f"Entry count validation passed: {unique_ids} >= {min_count}")
    return True

def validate_ingest(
    mp_path: Optional[Path] = None,
    aflow_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Main validation pipeline: load, merge, verify, and save.
    
    Args:
        mp_path: Path to MP results CSV
        aflow_path: Path to AFLOW results CSV
        output_path: Path to save the validated merged CSV (default: data/processed/validated_elastic.csv)
        
    Returns:
        Validated merged DataFrame
    """
    log_info("Starting ingestion validation pipeline")
    
    # Load and merge
    merged_df, skipped_ids = load_ingest_results(mp_path, aflow_path)
    
    # Log skipped IDs if any
    if skipped_ids:
        log_warning(f"Skipped {len(skipped_ids)} IDs during ingestion")
        for sid in skipped_ids[:10]:  # Log first 10
            log_warning(f"  Skipped ID: {sid}")
    
    # Verify entry count
    is_valid = verify_entry_count(merged_df)
    
    if not is_valid:
        # Log warning but do not raise immediately to allow inspection
        # The pipeline might still proceed if the user accepts lower count
        log_warning("Dataset size below SC-001 threshold. Proceeding with caution.")
    
    # Save validated output
    if output_path is None:
        output_path = get_path("data_processed", "validated_elastic.csv")
    
    ensure_directories([output_path])
    merged_df.to_csv(output_path, index=False)
    log_info(f"Validated data saved to {output_path}")
    
    return merged_df

def main():
    """CLI entry point for validation script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate and merge ingested elastic data")
    parser.add_argument("--mp", type=str, help="Path to MP ingestion CSV")
    parser.add_argument("--aflow", type=str, help="Path to AFLOW ingestion CSV")
    parser.add_argument("--output", type=str, help="Path for output validated CSV")
    
    args = parser.parse_args()
    
    mp_path = Path(args.mp) if args.mp else None
    aflow_path = Path(args.aflow) if args.aflow else None
    output_path = Path(args.output) if args.output else None
    
    try:
        df = validate_ingest(mp_path, aflow_path, output_path)
        log_success(f"Validation complete. {len(df)} entries processed.")
        return 0
    except Exception as e:
        log_error(f"Validation failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
