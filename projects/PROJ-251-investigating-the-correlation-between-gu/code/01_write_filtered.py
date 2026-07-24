import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any

# Ensure we can import from the project root
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_processed_path, get_raw_path, get_random_seed
from utils.logging_config import get_logger, log_exclusion_count, log_sample_size
from utils.validators import validate_dataframe_not_empty
import pandas as pd
import numpy as np

logger = get_logger(__name__)

def load_intermediate_data() -> pd.DataFrame:
    """
    Load the merged intermediate dataset.
    Prefers the Strategy B merged output (T011d) if it exists,
    otherwise falls back to Strategy A raw outputs if they were merged elsewhere.
    Based on task flow: T011d produces the merged data.
    """
    # Expected path from T011d logic (Strategy B merge)
    merged_path = get_processed_path("merged_strategy_b.csv")
    
    # Fallback if T011d output isn't exactly at that name but exists in processed
    if not merged_path.exists():
        processed_dir = get_processed_path()
        # Look for any merged csv
        candidates = list(processed_dir.glob("merged*.csv"))
        if candidates:
            merged_path = candidates[0]
        else:
            # Try raw directory if merge happened there (unlikely per spec but safe)
            raw_dir = get_raw_path()
            candidates = list(raw_dir.glob("merged*.csv"))
            if candidates:
                merged_path = candidates[0]
    
    if not merged_path.exists():
        raise FileNotFoundError(
            f"Intermediate merged data not found at {merged_path}. "
            "Ensure T011d (merge) or T011a (Strategy A download) has completed successfully."
        )
    
    logger.info(f"Loading intermediate data from {merged_path}")
    df = pd.read_csv(merged_path)
    
    # Basic sanity check
    if df.empty:
        raise ValueError("Loaded intermediate data is empty.")
    
    return df

def write_final_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """
    Write the final filtered dataset to CSV.
    """
    logger.info(f"Writing final filtered dataset to {output_path}")
    df.to_csv(output_path, index=False)
    logger.info("Write completed successfully.")

def log_exclusion_statistics(
    original_count: int, 
    final_count: int, 
    excluded_reasons: Dict[str, int],
    output_path: Path
) -> None:
    """
    Log exclusion counts and statistics to a JSON file and logger.
    """
    stats = {
        "original_count": original_count,
        "final_count": final_count,
        "excluded_count": original_count - final_count,
        "exclusion_breakdown": excluded_reasons,
        "timestamp": str(pd.Timestamp.now())
    }
    
    # Log to console/logger
    logger.info(f"Exclusion Summary: {original_count} -> {final_count} rows")
    for reason, count in excluded_reasons.items():
        log_exclusion_count(reason, count)
    
    log_sample_size(final_count)
    
    # Write to JSON file
    stats_path = output_path.parent / "exclusion_log.json"
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Exclusion statistics saved to {stats_path}")

def run_write_filtered() -> None:
    """
    Main entry point for T016:
    1. Load intermediate data (from T011d or equivalent).
    2. Apply filtering logic (T012: exclude missing titers, T014a: N>=50 check).
    3. Write to data/processed/filtered_data.csv.
    4. Log exclusion counts.
    """
    logger.info("Starting T016: Write Filtered Dataset")
    
    # 1. Load Data
    try:
        df = load_intermediate_data()
    except Exception as e:
        logger.error(f"Failed to load intermediate data: {e}")
        raise
    
    original_count = len(df)
    excluded_reasons: Dict[str, int] = {}
    
    # 2. Apply Filtering Logic (T012: Exclude subjects missing titers)
    # Identify columns
    titer_cols = [col for col in df.columns if 'titer' in col.lower()]
    if not titer_cols:
        # Fallback to generic names if specific ones aren't found
        titer_cols = ['titer_baseline', 'titer_post']
    
    # Filter out rows where any titer column is null or NaN
    initial_null_count = 0
    for col in titer_cols:
        if col in df.columns:
            null_count = df[col].isna().sum()
            initial_null_count += null_count
        else:
            logger.warning(f"Expected titer column {col} not found in dataset.")
    
    # Drop rows with any NaN in titer columns
    df_filtered = df.dropna(subset=titer_cols)
    
    if initial_null_count > 0:
        excluded_reasons["missing_titer_values"] = initial_null_count
    
    # 3. Validation Gate: N >= 50 (T014a)
    if len(df_filtered) < 50:
        msg = f"Sample size {len(df_filtered)} is less than minimum required 50 after filtering."
        logger.error(msg)
        raise ValueError(msg)
    
    # 4. Dynamic Sampling Check (T014b) - Only if memory is constrained
    # Note: T014b logic is usually executed before writing, but here we ensure
    # we don't write more than needed if memory is tight.
    try:
        import psutil
        available_mem = psutil.virtual_memory().available
        # Threshold: 6GB
        if available_mem < 6 * 1024 * 1024 * 1024:
            logger.warning("Memory constrained. Applying random sampling.")
            # Sample to fit, keeping at least 50
            target_size = max(50, int(len(df_filtered) * 0.5)) # Heuristic
            df_filtered = df_filtered.sample(
                n=target_size, 
                random_state=get_random_seed()
            )
            excluded_reasons["memory_sampling"] = original_count - len(df_filtered)
    except ImportError:
        logger.warning("psutil not installed. Skipping memory-based sampling check.")
    
    final_count = len(df_filtered)
    
    # 5. Write Output
    output_path = get_processed_path("filtered_data.csv")
    write_final_dataset(df_filtered, output_path)
    
    # 6. Log Statistics
    log_exclusion_statistics(original_count, final_count, excluded_reasons, output_path)
    
    logger.info("T016 completed successfully.")

if __name__ == "__main__":
    run_write_filtered()
