import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Create necessary output directories if they don't exist."""
    output_dir = Path("data/raw/filtered")
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directory exists: {output_dir}")
    return output_dir

def load_raw_dataset(dataset_name: str, data_dir: Path) -> Optional[pd.DataFrame]:
    """
    Load a raw dataset from disk.
    Expects parquet files in data/raw/<dataset_name>/
    """
    source_dir = data_dir / dataset_name
    parquet_files = list(source_dir.glob("*.parquet"))
    
    if not parquet_files:
        logger.warning(f"No parquet files found in {source_dir}")
        return None

    # Load the first available parquet file
    df = pd.read_parquet(parquet_files[0])
    logger.info(f"Loaded {len(df)} rows from {dataset_name}")
    return df

def filter_dialogues(df: pd.DataFrame, source: str) -> tuple[pd.DataFrame, Dict[str, int]]:
    """
    Filter dialogues to exclude those missing 'quality_rating' or chatbot utterances.
    
    Args:
        df: DataFrame containing dialogue data
        source: Name of the source dataset for logging
        
    Returns:
        Tuple of (filtered_df, exclusion_counts)
    """
    if df is None or df.empty:
        logger.warning(f"Empty or None dataframe for {source}, returning empty")
        return pd.DataFrame(), {"missing_quality_rating": 0, "missing_utterances": 0, "total_excluded": 0}

    initial_count = len(df)
    exclusion_counts = {
        "missing_quality_rating": 0,
        "missing_utterances": 0,
        "total_excluded": 0
    }

    # Check for quality_rating column
    if 'quality_rating' not in df.columns:
        logger.warning(f"Column 'quality_rating' not found in {source}. Excluding all rows.")
        exclusion_counts["missing_quality_rating"] = initial_count
        exclusion_counts["total_excluded"] = initial_count
        return pd.DataFrame(), exclusion_counts

    # Filter out rows missing quality_rating
    df_with_quality = df.dropna(subset=['quality_rating'])
    missing_quality_count = initial_count - len(df_with_quality)
    exclusion_counts["missing_quality_rating"] = missing_quality_count
    
    logger.info(f"{source}: Excluded {missing_quality_count} dialogues missing 'quality_rating'")

    # Check for utterances column
    if 'utterances' not in df_with_quality.columns:
        logger.warning(f"Column 'utterances' not found in {source}. Excluding all remaining rows.")
        exclusion_counts["missing_utterances"] = len(df_with_quality)
        exclusion_counts["total_excluded"] = len(df_with_quality)
        return pd.DataFrame(), exclusion_counts

    # Filter out rows with missing or empty utterances
    # Assuming utterances is a list or string; exclude if NaN, empty list, or empty string
    def has_valid_utterances(val):
        if pd.isna(val):
            return False
        if isinstance(val, list):
            return len(val) > 0
        if isinstance(val, str):
            return len(val.strip()) > 0
        return True

    df_with_utterances = df_with_quality[df_with_quality['utterances'].apply(has_valid_utterances)]
    missing_utterances_count = len(df_with_quality) - len(df_with_utterances)
    exclusion_counts["missing_utterances"] = missing_utterances_count
    exclusion_counts["total_excluded"] = missing_quality_count + missing_utterances_count

    logger.info(f"{source}: Excluded {missing_utterances_count} dialogues missing chatbot utterances")
    logger.info(f"{source}: Final filtered count: {len(df_with_utterances)} / {initial_count}")

    return df_with_utterances, exclusion_counts

def save_results(filtered_dfs: List[pd.DataFrame], exclusion_logs: List[Dict[str, Any]], output_dir: Path):
    """
    Save filtered datasets and exclusion logs.
    
    Args:
        filtered_dfs: List of filtered DataFrames
        exclusion_logs: List of exclusion count dictionaries
        output_dir: Directory to save results
    """
    if not filtered_dfs:
        logger.warning("No filtered data to save.")
        return

    # Save merged filtered data
    if len(filtered_dfs) == 1:
        final_df = filtered_dfs[0]
    else:
        final_df = pd.concat(filtered_dfs, ignore_index=True)
    
    output_path = output_dir / "filtered_dialogues.parquet"
    final_df.to_parquet(output_path, index=False)
    logger.info(f"Saved filtered dialogues to {output_path} ({len(final_df)} rows)")

    # Save exclusion log
    log_path = output_dir / "exclusion_counts.json"
    with open(log_path, 'w') as f:
        json.dump(exclusion_logs, f, indent=2)
    logger.info(f"Saved exclusion counts to {log_path}")

def main():
    """
    Main entry point for filtering dialogues.
    Processes all available raw datasets (HCI_P2, Persona-Chat, EmpatheticDialogues).
    """
    logger.info("Starting dialogue filtering process...")
    
    data_dir = Path("data/raw")
    output_dir = ensure_directories()
    
    # List of datasets to process
    datasets = [
        "hci_p2",
        "persona_chat", 
        "empathetic_dialogues"
    ]
    
    filtered_dfs = []
    exclusion_logs = []
    
    for dataset_name in datasets:
        dataset_path = data_dir / dataset_name
        if not dataset_path.exists():
            logger.info(f"Skipping {dataset_name}: directory does not exist")
            continue
        
        logger.info(f"Processing {dataset_name}...")
        df = load_raw_dataset(dataset_name, data_dir)
        
        if df is not None:
            filtered_df, counts = filter_dialogues(df, dataset_name)
            if not filtered_df.empty:
                filtered_dfs.append(filtered_df)
            exclusion_logs.append({
                "dataset": dataset_name,
                "counts": counts
            })
        else:
            exclusion_logs.append({
                "dataset": dataset_name,
                "counts": {"error": "Failed to load dataset", "total_excluded": 0}
            })
    
    if filtered_dfs:
        save_results(filtered_dfs, exclusion_logs, output_dir)
        logger.info("Filtering process completed successfully.")
    else:
        logger.warning("No data remained after filtering. Check exclusion logs.")
        # Still save the log even if no data
        save_results([], exclusion_logs, output_dir)

if __name__ == "__main__":
    main()
