import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any

from config import get_config, get_mmse_threshold
from utils import setup_logging, log_info, log_warning, log_error, get_timestamp

# Configure logging
logger = logging.getLogger(__name__)

def get_config_paths() -> Dict[str, Path]:
    """Get file paths from config."""
    config = get_config()
    return {
        "score_filtered": Path(config["data_processed"]) / "cleaned_score_filtered.csv",
        "mmse_flag": Path(config["data_processed"]) / "mmse_flag.json",
        "exclusion_counts": Path(config["data_processed"]) / "exclusion_counts.json",
        "cleaned_dataset": Path(config["data_processed"]) / "cleaned_dataset.csv",
        "cleaned_dataset_no_mmse": Path(config["data_processed"]) / "cleaned_dataset_no_mmse.csv",
    }

def load_score_filtered_dataset(path: Path) -> pd.DataFrame:
    """Load the score-filtered dataset."""
    if not path.exists():
        raise FileNotFoundError(f"Score filtered dataset not found at {path}")
    log_info(logger, f"Loading score filtered dataset from {path}")
    return pd.read_csv(path)

def load_mmse_flag(path: Path) -> bool:
    """Load the MMSE flag from JSON."""
    if not path.exists():
        raise FileNotFoundError(f"MMSE flag file not found at {path}")
    log_info(logger, f"Loading MMSE flag from {path}")
    with open(path, 'r') as f:
        data = json.load(f)
    return data.get("has_mmse", False)

def filter_mmse(df: pd.DataFrame, threshold: int) -> pd.DataFrame:
    """Filter dataset by MMSE >= threshold."""
    if "MMSE" not in df.columns:
        log_warning(logger, "MMSE column not found in dataset, returning full dataset")
        return df
    
    initial_count = len(df)
    filtered_df = df[df["MMSE"] >= threshold].copy()
    final_count = len(filtered_df)
    excluded_count = initial_count - final_count

    if excluded_count > 0:
        log_info(logger, f"Filtered {excluded_count} records with MMSE < {threshold}")
    else:
        log_info(logger, f"No records excluded based on MMSE threshold {threshold}")
    
    return filtered_df

def save_cleaned_dataset(df: pd.DataFrame, path: Path) -> None:
    """Save the primary cleaned dataset."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    log_info(logger, f"Saved primary cleaned dataset to {path} ({len(df)} records)")

def save_no_mmse_dataset(df: pd.DataFrame, path: Path) -> None:
    """Save the dataset without MMSE filtering (for robustness checks)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    log_info(logger, f"Saved no-MMSE dataset to {path} ({len(df)} records)")

def update_exclusion_counts(
    current_counts: Dict[str, Any], 
    mmse_excluded_count: int
) -> Dict[str, Any]:
    """Update exclusion counts with MMSE exclusion data."""
    if mmse_excluded_count > 0:
        current_counts["ERR_MMSE_IMPAIRED"] = mmse_excluded_count
    else:
        current_counts["ERR_MMSE_IMPAIRED"] = 0
    return current_counts

def save_exclusion_counts(counts: Dict[str, Any], path: Path) -> None:
    """Save exclusion counts to JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(counts, f, indent=2)
    log_info(logger, f"Updated exclusion counts at {path}")

def load_exclusion_counts(path: Path) -> Dict[str, Any]:
    """Load existing exclusion counts."""
    if not path.exists():
        return {}
    with open(path, 'r') as f:
        return json.load(f)

def main() -> None:
    """Main execution for T012e: MMSE Exclusion and Robustness Prep."""
    setup_logging()
    log_info(logger, "Starting T012e: MMSE Exclusion and Robustness Prep")

    paths = get_config_paths()
    
    try:
        # Load input data
        df_score_filtered = load_score_filtered_dataset(paths["score_filtered"])
        has_mmse = load_mmse_flag(paths["mmse_flag"])
        
        # Load existing exclusion counts
        exclusion_counts = load_exclusion_counts(paths["exclusion_counts"])
        
        # Get MMSE threshold from config
        mmse_threshold = get_mmse_threshold()
        
        mmse_excluded_count = 0

        if has_mmse:
            log_info(logger, "MMSE data is present. Filtering for MMSE >= 24.")
            df_primary = filter_mmse(df_score_filtered, mmse_threshold)
            mmse_excluded_count = len(df_score_filtered) - len(df_primary)
            save_cleaned_dataset(df_primary, paths["cleaned_dataset"])
        else:
            log_info(logger, "MMSE data is NOT present. Copying score-filtered dataset as primary.")
            save_cleaned_dataset(df_score_filtered, paths["cleaned_dataset"])
        
        # Always generate the no-MMSE dataset for robustness checks
        log_info(logger, "Generating cleaned_dataset_no_mmse.csv for robustness analysis.")
        save_no_mmse_dataset(df_score_filtered, paths["cleaned_dataset_no_mmse"])
        
        # Update and save exclusion counts
        exclusion_counts = update_exclusion_counts(exclusion_counts, mmse_excluded_count)
        save_exclusion_counts(exclusion_counts, paths["exclusion_counts"])
        
        log_info(logger, "T012e completed successfully.")
        
    except FileNotFoundError as e:
        log_error(logger, f"Required input file missing: {e}")
        raise
    except Exception as e:
        log_error(logger, f"Error during T012e execution: {e}")
        raise

if __name__ == "__main__":
    main()
