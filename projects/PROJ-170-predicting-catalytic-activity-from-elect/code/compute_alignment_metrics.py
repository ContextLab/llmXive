"""
T013: Compute Alignment Success Rate (SC-002).

Calculates the alignment success rate defined as:
(matched entries / total entries in the active experimental dataset, i.e., OC20).

This metric is logged explicitly in `outputs/alignment_metrics.json`.

Dependencies:
- T013b: Unified DataFrame with entry_ids must exist at data/processed/unified_dataset.csv
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd

# Import from existing project modules
from config import get_project_root, get_data_path, get_output_path
from logging_config import setup_logging, get_logger

# --- Constants ---
UNIFIED_DATASET_PATH = "data/processed/unified_dataset.csv"
OUTPUT_METRICS_PATH = "outputs/alignment_metrics.json"

def load_unified_dataframe() -> pd.DataFrame:
    """Load the unified dataframe generated in T013b."""
    project_root = get_project_root()
    file_path = project_root / UNIFIED_DATASET_PATH

    if not file_path.exists():
        raise FileNotFoundError(
            f"Unified dataset not found at {file_path}. "
            "Please ensure T013b (construct_unified_dataframe) has been completed."
        )

    logger = get_logger(__name__)
    logger.info(f"Loading unified dataset from {file_path}")
    df = pd.read_csv(file_path)
    
    # Basic validation
    required_cols = ["entry_id", "composition", "surface_facet"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Unified dataset missing required columns: {missing_cols}")
    
    return df

def compute_alignment_success_rate(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute the alignment success rate (SC-002).

    Logic:
    1. Total entries = count of rows in the unified dataset (which represents the active OC20 set).
    2. Matched entries = count of rows where the alignment process was successful.
       In the context of T013b, the unified dataframe *is* the result of the alignment/merging.
       If T013b successfully constructed the unified dataframe by merging sources,
       all rows in this dataframe represent "matched" entries that satisfied the join keys.
       
       However, if T013b included rows that failed to match (e.g. kept from left join with NaNs),
       we must filter for valid matches. Assuming T013b produces a clean dataframe of matches:
       Matched = Total rows.
       
       To be robust against potential NaNs in key fields from a previous step:
       We count rows where 'entry_id' is not null/empty.
    """
    logger = get_logger(__name__)
    
    total_entries = len(df)
    
    # Filter for valid entries (non-null entry_id)
    # If T013b produced a clean list of matches, this count equals total_entries.
    # If it included unmatched rows with null IDs, we exclude them.
    valid_mask = df["entry_id"].notna() & (df["entry_id"] != "")
    matched_entries = valid_mask.sum()
    
    if total_entries == 0:
        success_rate = 0.0
    else:
        success_rate = matched_entries / total_entries

    metrics = {
        "total_entries_in_active_dataset": int(total_entries),
        "matched_entries": int(matched_entries),
        "alignment_success_rate": float(success_rate),
        "description": "Ratio of matched entries to total entries in the active experimental dataset (OC20) as per SC-002."
    }
    
    logger.info(f"Alignment Success Rate Computed: {success_rate:.4f} ({matched_entries}/{total_entries})")
    return metrics

def save_metrics(metrics: Dict[str, Any]) -> None:
    """Save metrics to the output JSON file."""
    project_root = get_project_root()
    output_path = project_root / OUTPUT_METRICS_PATH
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)
    
    logger = get_logger(__name__)
    logger.info(f"Alignment metrics saved to {output_path}")

def main():
    """Main entry point for T013."""
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)
    
    try:
        # 1. Load Data
        df = load_unified_dataframe()
        
        # 2. Compute Metric
        metrics = compute_alignment_success_rate(df)
        
        # 3. Save Output
        save_metrics(metrics)
        
        logger.info("T013 completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error during alignment metric computation: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())