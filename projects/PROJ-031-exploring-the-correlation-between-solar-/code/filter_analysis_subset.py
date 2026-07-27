"""
Filter non-recurrent storms from the primary aligned events dataset.

This module implements the logic to create a derived analysis subset by
excluding recurrent storms identified in the primary dataset. This satisfies
the 'no exclusion' rule for the primary dataset while enabling the correlation
analysis requirement in US2.
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def filter_non_recurrent_storms(
    input_path: str,
    output_path: str,
    recurrent_flag_column: str = 'is_recurrent'
) -> pd.DataFrame:
    """
    Filter the aligned events dataset to exclude recurrent storms.
    
    Args:
        input_path: Path to the primary aligned_events.csv file
        output_path: Path where the filtered analysis_subset.csv will be written
        recurrent_flag_column: Name of the column containing recurrent activity flags
        
    Returns:
        DataFrame containing only non-recurrent storms
        
    Raises:
        FileNotFoundError: If the input file does not exist
        ValueError: If the recurrent flag column is not found in the dataset
        RuntimeError: If the filtering results in an empty dataset
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading aligned events from {input_path}")
    df = pd.read_csv(input_path)
    
    if recurrent_flag_column not in df.columns:
        raise ValueError(
            f"Recurrent flag column '{recurrent_flag_column}' not found in dataset. "
            f"Available columns: {list(df.columns)}"
        )
    
    logger.info(f"Filtering out recurrent storms (flag={recurrent_flag_column})")
    total_events = len(df)
    
    # Filter: keep only rows where is_recurrent is False, NaN, or 0
    # Assuming True/1 indicates recurrent activity
    mask = ~(df[recurrent_flag_column].astype(bool))
    filtered_df = df[mask].copy()
    
    recurrent_count = total_events - len(filtered_df)
    non_recurrent_count = len(filtered_df)
    
    logger.info(f"Total events: {total_events}")
    logger.info(f"Recurrent events excluded: {recurrent_count}")
    logger.info(f"Non-recurrent events retained: {non_recurrent_count}")
    
    if non_recurrent_count == 0:
        raise RuntimeError(
            "Filtering resulted in an empty dataset. "
            "Check if all events were flagged as recurrent or if the flag column is incorrect."
        )
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Writing analysis subset to {output_path}")
    filtered_df.to_csv(output_path, index=False)
    
    logger.info(f"Successfully created analysis subset with {non_recurrent_count} events")
    
    return filtered_df

def main():
    """Main entry point for the filter analysis subset script."""
    parser = argparse.ArgumentParser(
        description='Filter non-recurrent storms from aligned events dataset'
    )
    parser.add_argument(
        '--input',
        type=str,
        default='data/processed/aligned_events.csv',
        help='Path to the input aligned_events.csv file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/processed/analysis_subset.csv',
        help='Path for the output analysis_subset.csv file'
    )
    parser.add_argument(
        '--flag-column',
        type=str,
        default='is_recurrent',
        help='Name of the column containing recurrent activity flags'
    )
    
    args = parser.parse_args()
    
    try:
        filter_non_recurrent_storms(
            input_path=args.input,
            output_path=args.output,
            recurrent_flag_column=args.flag_column
        )
        logger.info("Filtering completed successfully")
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
