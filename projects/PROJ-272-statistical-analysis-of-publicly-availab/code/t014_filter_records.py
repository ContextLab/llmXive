"""
Task T014: Filter Records
Implements function to filter records where label is null OR text length < 50 words.
Logs excluded records with reason codes to data/interim/exclusions.log.
"""
import logging
import os
import json
from pathlib import Path
from typing import Tuple, List, Dict, Any
import pandas as pd

from config import get_path

logger = logging.getLogger(__name__)

def filter_records(input_path: Path, output_path: Path, exclusions_log_path: Path) -> Tuple[int, int]:
    """
    Filter records based on label validity and text length.
    
    Args:
        input_path: Path to input CSV with cleaned transcripts
        output_path: Path to save filtered dataset
        exclusions_log_path: Path to log excluded records
        
    Returns:
        Tuple of (filtered_count, excluded_count)
    """
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    initial_count = len(df)
    logger.info(f"Initial record count: {initial_count}")
    
    exclusion_reasons = []
    valid_indices = []
    
    # Iterate and filter
    for idx, row in df.iterrows():
        # Check label
        label = row.get('label')
        if label is None or (isinstance(label, float) and pd.isna(label)):
            exclusion_reasons.append({
                'participant_id': row.get('participant_id', 'UNKNOWN'),
                'reason': 'MISSING_LABEL',
                'original_index': idx
            })
            continue
        
        # Check text length (word count)
        text = row.get('text', '')
        if not isinstance(text, str):
            text = str(text)
        
        word_count = len(text.split())
        
        if word_count < 50:
            exclusion_reasons.append({
                'participant_id': row.get('participant_id', 'UNKNOWN'),
                'reason': 'TOO_SHORT',
                'word_count': word_count,
                'original_index': idx
            })
            continue
        
        valid_indices.append(idx)
    
    # Log exclusions
    exclusions_log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(exclusions_log_path, 'w', encoding='utf-8') as f:
        for reason in exclusion_reasons:
            f.write(json.dumps(reason) + '\n')
    
    # Filter dataset
    if len(valid_indices) > 0:
        filtered_df = df.iloc[valid_indices].reset_index(drop=True)
    else:
        filtered_df = pd.DataFrame(columns=df.columns)
    
    # Save filtered dataset
    output_path.parent.mkdir(parents=True, exist_ok=True)
    filtered_df.to_csv(output_path, index=False)
    
    filtered_count = len(filtered_df)
    excluded_count = initial_count - filtered_count
    
    logger.info(f"Filtered dataset saved to {output_path}")
    logger.info(f"Filtered count: {filtered_count}")
    logger.info(f"Excluded count: {excluded_count}")
    
    # Log reasons summary
    reason_counts = {}
    for reason in exclusion_reasons:
        r = reason['reason']
        reason_counts[r] = reason_counts.get(r, 0) + 1
    
    for reason, count in reason_counts.items():
        logger.info(f"Excluded {count} records due to {reason}")
    
    return filtered_count, excluded_count

def main():
    """Main entry point for T014."""
    # Setup logging
    from utils import setup_logging
    setup_logging()
    
    # Define paths
    input_path = get_path('data/interim/cleaned_transcripts.csv')
    output_path = get_path('data/interim/cleaned_adress.csv')
    exclusions_log_path = get_path('data/interim/exclusions.log')
    
    # Verify input exists
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Run filtering
    filtered_count, excluded_count = filter_records(
        input_path=input_path,
        output_path=output_path,
        exclusions_log_path=exclusions_log_path
    )
    
    logger.info(f"T014 completed. Filtered: {filtered_count}, Excluded: {excluded_count}")

if __name__ == '__main__':
    main()
