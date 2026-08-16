import argparse
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd
import numpy as np

def setup_logging():
    """Configure logging for the fidelity loss module."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def load_raw_data(logger, input_path):
    """
    Load the raw data from the specified parquet file.
    
    Args:
        logger: Logger instance
        input_path: Path to the input parquet file (output of T012/T013)
        
    Returns:
        DataFrame with raw data
    """
    logger.info(f"Loading raw data from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} rows")
    return df

def calculate_fidelity_loss(logger, df):
    """
    Calculate dimensional fidelity loss for each sample.
    
    1. Compute MAE between student_scalar and human-annotated score 
       for the sample's primary_dimension.
    2. Exclude samples where primary_dimension is null, 
       human annotation for that dimension is missing, or 
       student_scalar is missing.
    
    Args:
        logger: Logger instance
        df: DataFrame with raw data
        
    Returns:
        Tuple of (cleaned_df, excluded_reasons)
    """
    logger.info("Calculating dimensional fidelity loss")
    
    # Identify excluded samples
    excluded_reasons = []
    cleaned_rows = []
    
    for idx, row in df.iterrows():
        exclusion_reason = None
        
        # Check if primary_dimension is null
        primary_dim = row.get('primary_dimension')
        if pd.isna(primary_dim) or primary_dim is None:
            exclusion_reason = 'null_primary_dimension'
        
        # Check if student_scalar is missing
        student_scalar = row.get('student_scalar')
        if pd.isna(student_scalar) or student_scalar is None:
            exclusion_reason = 'missing_student_scalar'
        
        # Check if human annotations for primary dimension exist
        if not exclusion_reason:
            human_annotations = row.get('human_annotations', {})
            if not isinstance(human_annotations, dict):
                exclusion_reason = 'invalid_human_annotations'
            elif primary_dim not in human_annotations:
                exclusion_reason = 'missing_human_annotation_dimension'
            elif pd.isna(human_annotations.get(primary_dim)):
                exclusion_reason = 'null_human_annotation_value'
        
        if exclusion_reason:
            excluded_reasons.append({
                'sample_index': idx,
                'reason': exclusion_reason
            })
        else:
            # Calculate fidelity loss
            human_score = human_annotations[primary_dim]
            fidelity_loss = abs(student_scalar - human_score)
            
            # Create cleaned row with fidelity loss
            cleaned_row = row.copy()
            cleaned_row['fidelity_loss'] = fidelity_loss
            cleaned_rows.append(cleaned_row)
    
    logger.info(f"Excluded {len(excluded_reasons)} samples due to missing data")
    logger.info(f"Retained {len(cleaned_rows)} samples for fidelity loss calculation")
    
    if len(cleaned_rows) == 0:
        logger.warning("No samples retained for fidelity loss calculation")
        cleaned_df = pd.DataFrame()
    else:
        cleaned_df = pd.DataFrame(cleaned_rows)
    
    return cleaned_df, excluded_reasons

def save_cleaned_data(logger, df, output_path):
    """
    Save the cleaned dataframe with fidelity loss to parquet.
    
    Args:
        logger: Logger instance
        df: DataFrame with fidelity loss calculated
        output_path: Path to save the cleaned data
    """
    logger.info(f"Saving cleaned data to {output_path}")
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")

def save_summary(logger, df, excluded_reasons, summary_path):
    """
    Calculate and save summary statistics for fidelity loss.
    
    Args:
        logger: Logger instance
        df: DataFrame with fidelity loss
        excluded_reasons: List of exclusion reasons
        summary_path: Path to save the summary JSON
    """
    logger.info("Calculating fidelity loss summary statistics")
    
    if len(df) > 0:
        fidelity_loss_values = df['fidelity_loss'].dropna()
        summary = {
            'mean': float(fidelity_loss_values.mean()) if len(fidelity_loss_values) > 0 else None,
            'median': float(fidelity_loss_values.median()) if len(fidelity_loss_values) > 0 else None,
            'std': float(fidelity_loss_values.std()) if len(fidelity_loss_values) > 0 else None,
            'min': float(fidelity_loss_values.min()) if len(fidelity_loss_values) > 0 else None,
            'max': float(fidelity_loss_values.max()) if len(fidelity_loss_values) > 0 else None,
            'count': int(len(fidelity_loss_values)),
            'excluded_count': len(excluded_reasons),
            'excluded_reasons': excluded_reasons
        }
    else:
        summary = {
            'mean': None,
            'median': None,
            'std': None,
            'min': None,
            'max': None,
            'count': 0,
            'excluded_count': len(excluded_reasons),
            'excluded_reasons': excluded_reasons
        }
    
    logger.info(f"Summary: mean={summary['mean']}, median={summary['median']}, count={summary['count']}")
    
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Saved summary to {summary_path}")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Calculate dimensional fidelity loss')
    parser.add_argument(
        '--input',
        type=str,
        default='data/processed/raw_data.parquet',
        help='Path to input parquet file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/processed/cleaned_data.parquet',
        help='Path to output cleaned parquet file'
    )
    parser.add_argument(
        '--summary',
        type=str,
        default='data/processed/fidelity_loss_summary.json',
        help='Path to output summary JSON file'
    )
    return parser.parse_args()

def main():
    """Main entry point for fidelity loss calculation."""
    args = parse_args()
    logger = setup_logging()
    
    try:
        # Load raw data
        df = load_raw_data(logger, args.input)
        
        # Calculate fidelity loss
        cleaned_df, excluded_reasons = calculate_fidelity_loss(logger, df)
        
        # Save cleaned data
        save_cleaned_data(logger, cleaned_df, args.output)
        
        # Save summary
        save_summary(logger, cleaned_df, excluded_reasons, args.summary)
        
        logger.info("Fidelity loss calculation completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during fidelity loss calculation: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()