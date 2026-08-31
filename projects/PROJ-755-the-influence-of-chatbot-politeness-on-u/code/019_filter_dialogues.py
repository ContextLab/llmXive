"""
T019: Implement filtering logic to exclude dialogues missing `quality_rating` or chatbot utterances.

This script loads the raw HCI_P2 dataset (validated in T015a), filters out dialogues
that lack a `quality_rating` or have missing chatbot utterances, logs the counts of
excluded dialogues, and saves the filtered dataset to `data/raw/filtered/`.

Dependencies:
- T015a: HCI_P2 Validation (must have `data/raw/hci_p2/validation_status.json` with status "valid")

Outputs:
- data/raw/filtered/filtered_dialogues.parquet
- data/raw/filtered/exclusions_log.json
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
from datasets import load_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_HCI_P2_DIR = PROJECT_ROOT / "data" / "raw" / "hci_p2"
FILTERED_DIR = PROJECT_ROOT / "data" / "raw" / "filtered"
VALIDATION_STATUS_PATH = RAW_HCI_P2_DIR / "validation_status.json"

def ensure_directories() -> None:
    """Create output directories if they don't exist."""
    FILTERED_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory exists: {FILTERED_DIR}")

def load_raw_dataset() -> pd.DataFrame:
    """
    Load the raw HCI_P2 dataset from the validated source.
    
    The dataset is expected to be in `data/raw/hci_p2/`. We attempt to load
    it as a parquet file or CSV, falling back to HuggingFace if local files
    are missing (though T015 should have downloaded them).
    
    Returns:
        pd.DataFrame: The raw dataset.
    
    Raises:
        FileNotFoundError: If the dataset cannot be found or loaded.
    """
    # Check for local files first
    parquet_path = RAW_HCI_P2_DIR / "hci_p2.parquet"
    csv_path = RAW_HCI_P2_DIR / "hci_p2.csv"
    
    if parquet_path.exists():
        logger.info(f"Loading dataset from parquet: {parquet_path}")
        return pd.read_parquet(parquet_path)
    elif csv_path.exists():
        logger.info(f"Loading dataset from CSV: {csv_path}")
        return pd.read_csv(csv_path)
    else:
        # Fallback: Load from HuggingFace (should not happen if T015 succeeded)
        logger.warning("Local files not found. Attempting to load from HuggingFace (HCI_P2)...")
        try:
            dataset = load_dataset("HuggingFaceH4/hci_p2", split="train")
            df = dataset.to_pandas()
            # Save locally for future runs
            df.to_parquet(parquet_path, index=False)
            logger.info(f"Saved downloaded dataset to {parquet_path}")
            return df
        except Exception as e:
            logger.error(f"Failed to load dataset from HuggingFace: {e}")
            raise FileNotFoundError("Cannot load HCI_P2 dataset. Ensure T015 completed successfully.")

def filter_dialogues(df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Filter dialogues to exclude those missing `quality_rating` or chatbot utterances.
    
    Logic:
    1. Exclude rows where `quality_rating` is NaN or missing.
    2. Exclude dialogues where chatbot utterances are missing or empty.
       - We assume the dataset has a column `utterances` which is a list of utterance objects.
       - Each utterance object should have a `speaker` field (e.g., "user", "chatbot").
       - We check if at least one utterance in the dialogue is from the chatbot.
    
    Args:
        df (pd.DataFrame): The raw dataset.
    
    Returns:
        tuple[pd.DataFrame, Dict[str, Any]]: Filtered dataframe and exclusion statistics.
    """
    logger.info(f"Initial dataset size: {len(df)} rows")
    
    # Count missing quality_rating
    missing_quality = df['quality_rating'].isna().sum()
    logger.info(f"Dialogues missing `quality_rating`: {missing_quality}")
    
    # Filter out missing quality_rating
    df_filtered = df.dropna(subset=['quality_rating'])
    logger.info(f"After removing missing quality_rating: {len(df_filtered)} rows")
    
    # Filter out dialogues with missing chatbot utterances
    # Assuming `utterances` column contains a list of dicts with 'speaker' key
    def has_chatbot_utterance(utterances):
        """Check if the utterances list contains at least one chatbot utterance."""
        if not utterances or not isinstance(utterances, list):
            return False
        for utterance in utterances:
            if isinstance(utterance, dict) and utterance.get('speaker') == 'chatbot':
                return True
        return False
    
    # Apply filter
    before_chatbot_filter = len(df_filtered)
    df_filtered = df_filtered[df_filtered['utterances'].apply(has_chatbot_utterance)]
    missing_chatbot = before_chatbot_filter - len(df_filtered)
    logger.info(f"Dialogues missing chatbot utterances: {missing_chatbot}")
    logger.info(f"After removing missing chatbot utterances: {len(df_filtered)} rows")
    
    # Compile statistics
    exclusion_stats = {
        "initial_count": len(df),
        "missing_quality_rating": int(missing_quality),
        "missing_chatbot_utterances": int(missing_chatbot),
        "final_count": int(len(df_filtered)),
        "excluded_count": int(len(df) - len(df_filtered))
    }
    
    return df_filtered, exclusion_stats

def save_results(df_filtered: pd.DataFrame, exclusion_stats: Dict[str, Any]) -> None:
    """
    Save the filtered dataset and exclusion log.
    
    Args:
        df_filtered (pd.DataFrame): The filtered dataset.
        exclusion_stats (Dict[str, Any]): Statistics about excluded dialogues.
    """
    output_path = FILTERED_DIR / "filtered_dialogues.parquet"
    log_path = FILTERED_DIR / "exclusions_log.json"
    
    # Save filtered dataset
    df_filtered.to_parquet(output_path, index=False)
    logger.info(f"Saved filtered dataset to {output_path}")
    
    # Save exclusion log
    with open(log_path, 'w') as f:
        json.dump(exclusion_stats, f, indent=2)
    logger.info(f"Saved exclusion log to {log_path}")

def main() -> None:
    """Main entry point for T019."""
    logger.info("Starting T019: Filter dialogues")
    
    # Check validation status
    if not VALIDATION_STATUS_PATH.exists():
        logger.error(f"Validation status file not found: {VALIDATION_STATUS_PATH}")
        logger.error("T015a must complete successfully before running T019.")
        sys.exit(1)
    
    with open(VALIDATION_STATUS_PATH, 'r') as f:
        validation_status = json.load(f)
    
    if validation_status.get('status') != 'valid':
        logger.error(f"HCI_P2 validation status is '{validation_status.get('status')}'. Aborting.")
        logger.error("T015a must indicate 'valid' status before proceeding.")
        sys.exit(1)
    
    logger.info("HCI_P2 validation status is 'valid'. Proceeding with filtering.")
    
    # Ensure output directories
    ensure_directories()
    
    # Load raw dataset
    try:
        df_raw = load_raw_dataset()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Filter dialogues
    df_filtered, exclusion_stats = filter_dialogues(df_raw)
    
    # Save results
    save_results(df_filtered, exclusion_stats)
    
    logger.info("T019 completed successfully.")
    logger.info(f"Exclusion summary: {json.dumps(exclusion_stats, indent=2)}")

if __name__ == "__main__":
    main()