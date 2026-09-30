"""
T014: Filter Records
Filter records where label is null OR text length < 50 words.
Log excluded records with reason codes to data/interim/exclusions.log.
"""
import logging
import os
import json
from pathlib import Path
import pandas as pd
from config import get_path

# Configure logging for this specific task
logger = logging.getLogger(__name__)

def filter_records(input_path: Path, output_path: Path, exclusions_log_path: Path):
    """
    Filter the dataset based on FR-001 Edge Case requirements:
    1. Remove records where 'label' is null/missing.
    2. Remove records where 'text' length is < 50 words.
    
    Args:
        input_path: Path to the input CSV (cleaned transcripts).
        output_path: Path to save the filtered CSV.
        exclusions_log_path: Path to save the exclusion log.
    """
    logger.info(f"Loading data from {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Ensure 'label' and 'text' columns exist
    if 'label' not in df.columns:
        raise ValueError(f"Input CSV missing required column 'label'. Columns: {df.columns.tolist()}")
    if 'text' not in df.columns:
        raise ValueError(f"Input CSV missing required column 'text'. Columns: {df.columns.tolist()}")

    # Prepare exclusion log data
    exclusions = []
    
    # Count before filtering
    initial_count = len(df)
    logger.info(f"Total records before filtering: {initial_count}")

    # 1. Filter out null labels
    # Handle potential NaNs in label column
    label_mask = df['label'].notna()
    null_label_count = initial_count - label_mask.sum()
    
    if null_label_count > 0:
        null_label_ids = df[~label_mask].get('participant_id', df.index).tolist()
        for pid in null_label_ids:
            exclusions.append({
                'participant_id': pid,
                'reason_code': 'LABEL_NULL',
                'reason_detail': 'Label is missing or NaN'
            })
    
    # 2. Filter out short texts (< 50 words)
    # Apply label mask first to only check texts of valid records
    df_with_labels = df[label_mask].copy()
    
    # Word count function
    def count_words(text):
        if pd.isna(text) or not isinstance(text, str):
            return 0
        return len(str(text).split())
    
    df_with_labels['word_count'] = df_with_labels['text'].apply(count_words)
    
    short_text_mask = df_with_labels['word_count'] >= 50
    short_text_count = len(df_with_labels) - short_text_mask.sum()
    
    if short_text_count > 0:
        short_text_ids = df_with_labels[~short_text_mask].get('participant_id', df_with_labels.index).tolist()
        for pid in short_text_ids:
            exclusions.append({
                'participant_id': pid,
                'reason_code': 'TEXT_TOO_SHORT',
                'reason_detail': f'Text length ({df_with_labels.loc[df_with_labels.get("participant_id") == pid, "word_count"].values[0] if not df_with_labels[df_with_labels.get("participant_id") == pid].empty else "unknown"}) < 50 words'
            })
    
    # Apply final filtering
    # We need to combine the masks carefully. 
    # Start with the label mask, then apply the word count mask on the subset.
    # Since df_with_labels is a copy, we need to map the indices back or filter the original.
    # Easier approach: Filter original df using combined boolean logic.
    
    # Re-calculate word counts on the original df for the mask
    df['word_count'] = df['text'].apply(count_words)
    
    final_mask = df['label'].notna() & (df['word_count'] >= 50)
    
    filtered_df = df[final_mask].copy()
    filtered_df = filtered_df.drop(columns=['word_count']) # Drop helper column
    
    final_count = len(filtered_df)
    excluded_count = initial_count - final_count
    
    logger.info(f"Records excluded: {excluded_count} (Label Null: {null_label_count}, Text Short: {short_text_count})")
    logger.info(f"Records remaining: {final_count}")

    # Ensure output directories exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    exclusions_log_path.parent.mkdir(parents=True, exist_ok=True)

    # Save filtered dataset
    filtered_df.to_csv(output_path, index=False)
    logger.info(f"Filtered dataset saved to {output_path}")

    # Save exclusions log
    with open(exclusions_log_path, 'w', encoding='utf-8') as f:
        json.dump(exclusions, f, indent=2)
    logger.info(f"Exclusions log saved to {exclusions_log_path}")

    return filtered_df, exclusions

def main():
    """Entry point for T014."""
    # Setup basic logging if not already configured
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    # Define paths based on project structure
    # Input: Output of T013 (cleaned transcripts)
    input_path = get_path("data/interim/cleaned_transcripts.csv")
    # Output: Filtered dataset (interim step before final clean dataset)
    output_path = get_path("data/interim/cleaned_filtered_adress.csv")
    # Exclusions log
    exclusions_log_path = get_path("data/interim/exclusions.log")

    logger.info("Starting T014: Filter Records")
    
    try:
        filter_records(input_path, output_path, exclusions_log_path)
        logger.info("T014 completed successfully.")
    except Exception as e:
        logger.error(f"T014 failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
