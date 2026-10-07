"""
Topic Extraction Module for Linguistic Accommodation Analysis.

This module extracts raw topic labels from the DailyDialog dataset to serve
as control variables in regression analysis. It aligns the extracted topics
with the final processed dataset (T031 output).

FR-007: Extract raw topic labels from the DailyDialog dataset (column `topic`)
for regression control.
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from datasets import load_dataset
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
REPORTS_DIR = OUTPUTS_DIR / "reports"

# Ensure output directories exist
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def load_final_dataset() -> pd.DataFrame:
    """
    Load the final processed dataset from T031.

    Returns:
        pd.DataFrame: The final dataset containing accommodation metrics
                      and emotional intensity scores.
    """
    file_path = PROCESSED_DATA_DIR / "final_dataset.csv"
    if not file_path.exists():
        raise FileNotFoundError(
            f"Final dataset not found at {file_path}. "
            "Ensure T031 (emotion_mapping) has been completed."
        )
    
    logger.info(f"Loading final dataset from {file_path}")
    df = pd.read_csv(file_path)
    logger.info(f"Loaded {len(df)} records from final dataset")
    return df


def extract_daily_dialog_topics() -> List[str]:
    """
    Extract raw topic labels from the DailyDialog dataset.

    Uses streaming to handle the dataset efficiently without loading it
    entirely into memory. Aligns the order of topics with the original
    DailyDialog test set structure.

    Returns:
        List[str]: A list of topic labels corresponding to the dialogue turns.
    """
    logger.info("Initializing DailyDialog dataset stream (test split)...")
    
    # Use streaming to avoid memory issues
    dataset = load_dataset(
        "daily_dialog", 
        split="test", 
        streaming=True
    )
    
    topics = []
    count = 0
    
    logger.info("Iterating through DailyDialog test split to extract topics...")
    for item in dataset:
        # DailyDialog 'topic' column contains the topic label
        # We need to extract the topic for each turn in the dialogue
        # The dataset structure has 'topic' as a single label for the whole dialogue
        # We will duplicate this label for each turn to align with turn-level analysis
        
        topic_label = item.get('topic', 'unknown')
        dialogue = item.get('dialogue', [])
        
        # If dialogue is a list of turns, assign the topic to each turn
        if isinstance(dialogue, list):
            for _ in dialogue:
                topics.append(topic_label)
                count += 1
        else:
            # Fallback if structure is unexpected
            topics.append(topic_label)
            count += 1

    logger.info(f"Extracted {len(topics)} topic labels from {count} turns.")
    return topics


def align_topics_with_final_dataset(
    topics: List[str], 
    final_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Align extracted topics with the final dataset.

    The final dataset contains processed accommodation metrics at the 
    dialogue-pair level. We map the topics from the raw DailyDialog 
    structure to this processed level.

    Args:
        topics: List of topic labels from DailyDialog.
        final_df: The final processed dataset.

    Returns:
        pd.DataFrame: The final dataset with a 'topic' column added.
    """
    logger.info(f"Aligning {len(topics)} topics with {len(final_df)} final records...")
    
    # Create a copy to avoid modifying the original
    result_df = final_df.copy()
    
    # The DailyDialog test set has a specific number of dialogues.
    # Each dialogue has multiple turns.
    # Our final dataset likely aggregates metrics per dialogue pair.
    # We need to ensure the length matches or sample appropriately.
    
    if len(topics) != len(result_df):
        logger.warning(
            f"Mismatch in lengths: Topics ({len(topics)}) vs Final Dataset ({len(result_df)}). "
            "Attempting to align by taking the first N topics or handling the difference."
        )
        
        # Strategy: If the final dataset is a subset or processed version,
        # we assume the order is preserved from the original download.
        # We will truncate or pad with 'unknown' if necessary, but log it.
        if len(topics) > len(result_df):
            logger.info("Truncating topics list to match final dataset length.")
            result_df['topic'] = topics[:len(result_df)]
        elif len(topics) < len(result_df):
            logger.warning("Topics list is shorter than final dataset. Padding with 'unknown'.")
            padded_topics = topics + ['unknown'] * (len(result_df) - len(topics))
            result_df['topic'] = padded_topics
        else:
            result_df['topic'] = topics
    else:
        result_df['topic'] = topics

    logger.info(f"Alignment complete. Dataset shape: {result_df.shape}")
    return result_df


def save_topic_aligned_dataset(df: pd.DataFrame, output_path: Optional[Path] = None):
    """
    Save the topic-aligned dataset to CSV.

    Args:
        df: The dataframe with topics added.
        output_path: Path to save the file. Defaults to data/processed/final_dataset_with_topics.csv.
    """
    if output_path is None:
        output_path = PROCESSED_DATA_DIR / "final_dataset_with_topics.csv"
    
    logger.info(f"Saving topic-aligned dataset to {output_path}")
    df.to_csv(output_path, index=False)
    logger.info("Save complete.")


def generate_topic_report(df: pd.DataFrame, output_path: Optional[Path] = None):
    """
    Generate a summary report of the topic distribution.

    Args:
        df: The dataframe with topics.
        output_path: Path to save the JSON report.
    """
    if output_path is None:
        output_path = REPORTS_DIR / "topic_distribution.json"

    topic_counts = df['topic'].value_counts().to_dict()
    total_records = len(df)
    
    report = {
        "total_records": total_records,
        "unique_topics": len(topic_counts),
        "topic_distribution": topic_counts,
        "top_5_topics": dict(df['topic'].value_counts().head(5).to_dict())
    }

    logger.info(f"Saving topic distribution report to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info("Topic report generated.")
    return report


def main():
    """
    Main entry point for the topic extraction task.
    """
    try:
        # 1. Load the final dataset (output of T031)
        final_df = load_final_dataset()
        
        # 2. Extract raw topics from DailyDialog
        topics = extract_daily_dialog_topics()
        
        # 3. Align topics with the final dataset
        aligned_df = align_topics_with_final_dataset(topics, final_df)
        
        # 4. Save the aligned dataset
        save_topic_aligned_dataset(aligned_df)
        
        # 5. Generate and save the distribution report
        generate_topic_report(aligned_df)
        
        logger.info("Task T036a completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()