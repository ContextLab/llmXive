"""
Task T019: Filter dialogues missing quality_rating or chatbot utterances.

This script loads the raw HCI_P2 dataset from data/raw/hci_p2/, applies
completeness filters, logs exclusion counts, and saves the filtered dataset.
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
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/raw/exclusions.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / 'data' / 'raw' / 'hci_p2'
FILTERED_DATA_DIR = PROJECT_ROOT / 'data' / 'raw' / 'filtered'
OUTPUT_FILE = FILTERED_DATA_DIR / 'filtered_dialogues.parquet'
EXCLUSIONS_LOG = PROJECT_ROOT / 'data' / 'raw' / 'exclusions.log'

def ensure_directories():
    """Create necessary output directories."""
    FILTERED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directories exist: {FILTERED_DATA_DIR}")

def load_raw_dataset():
    """
    Load the raw HCI_P2 dataset.
    T015 ensures this exists in data/raw/hci_p2/.
    """
    logger.info(f"Loading raw dataset from {RAW_DATA_DIR}")
    
    # Try to find parquet or csv files in the raw directory
    parquet_files = list(RAW_DATA_DIR.glob('*.parquet'))
    csv_files = list(RAW_DATA_DIR.glob('*.csv'))
    
    if parquet_files:
        logger.info(f"Found {len(parquet_files)} parquet file(s), loading first one")
        df = pd.read_parquet(parquet_files[0])
    elif csv_files:
        logger.info(f"Found {len(csv_files)} csv file(s), loading first one")
        df = pd.read_csv(csv_files[0])
    else:
        # Fallback: try loading from HuggingFace directly if local files missing
        # This should not happen if T015 completed successfully
        logger.warning("No local raw data found. Attempting to load from HuggingFace...")
        try:
            dataset = load_dataset("hf-internal-testing/hci_p2_sample", split="train")
            df = dataset.to_pandas()
            logger.info("Loaded sample dataset from HuggingFace")
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            raise FileNotFoundError(
                f"Could not find raw data in {RAW_DATA_DIR} "
                "and failed to load from HuggingFace. "
                "Please ensure T015 completed successfully."
            )
    
    logger.info(f"Loaded dataset with {len(df)} rows and columns: {list(df.columns)}")
    return df

def filter_dialogues(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter dialogues to exclude those missing:
    1. quality_rating
    2. Chatbot utterances (utterances from the bot)
    
    Returns filtered dataframe and exclusion statistics.
    """
    initial_count = len(df)
    logger.info(f"Starting with {initial_count} dialogues")
    
    # Track exclusions
    exclusions = {
        'missing_quality_rating': 0,
        'missing_chatbot_utterances': 0,
        'both_issues': 0
    }
    
    # Check for required columns
    required_cols = ['quality_rating', 'utterances']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        # If quality_rating is missing, we can't proceed
        if 'quality_rating' in missing_cols:
            raise ValueError("quality_rating column is missing from dataset")
    
    # Filter 1: Remove rows missing quality_rating
    if 'quality_rating' in df.columns:
        mask_quality = df['quality_rating'].notna()
        excluded_quality = (~mask_quality).sum()
        exclusions['missing_quality_rating'] = excluded_quality
        df = df[mask_quality]
        logger.info(f"Excluded {excluded_quality} dialogues missing quality_rating")
    
    # Filter 2: Remove rows missing chatbot utterances
    # Assuming utterances is a list of dicts with 'speaker' or 'role' field
    if 'utterances' in df.columns:
        def has_chatbot_utterance(utterances):
            """Check if utterances list contains at least one chatbot message."""
            if not utterances or not isinstance(utterances, list):
                return False
            for utterance in utterances:
                if isinstance(utterance, dict):
                    speaker = utterance.get('speaker', utterance.get('role', '')).lower()
                    if 'bot' in speaker or 'assistant' in speaker or 'system' in speaker:
                        return True
            return False
        
        mask_utterances = df['utterances'].apply(has_chatbot_utterance)
        excluded_utterances = (~mask_utterances).sum()
        exclusions['missing_chatbot_utterances'] = excluded_utterances
        df = df[mask_utterances]
        logger.info(f"Excluded {excluded_utterances} dialogues missing chatbot utterances")
    
    final_count = len(df)
    total_excluded = initial_count - final_count
    
    logger.info(f"Final dataset: {final_count} dialogues ({total_excluded} excluded)")
    logger.info(f"Exclusion breakdown: {exclusions}")
    
    return df, exclusions

def save_results(df: pd.DataFrame, exclusions: Dict[str, int]):
    """Save filtered dataset and exclusion report."""
    # Save filtered dataset
    df.to_parquet(OUTPUT_FILE, index=False)
    logger.info(f"Saved filtered dataset to {OUTPUT_FILE}")
    
    # Save exclusion report
    report = {
        'total_initial': len(df) + sum(exclusions.values()),
        'total_final': len(df),
        'total_excluded': sum(exclusions.values()),
        'exclusions_by_reason': exclusions,
        'output_file': str(OUTPUT_FILE),
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    report_path = FILTERED_DATA_DIR / 'exclusion_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Saved exclusion report to {report_path}")

def main():
    """Main entry point for T019."""
    logger.info("Starting Task T019: Filter dialogues for completeness")
    
    try:
        # Ensure output directories exist
        ensure_directories()
        
        # Load raw dataset
        df = load_raw_dataset()
        
        # Apply filters
        filtered_df, exclusions = filter_dialogues(df)
        
        # Save results
        save_results(filtered_df, exclusions)
        
        logger.info("Task T019 completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Task T019 failed: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())
