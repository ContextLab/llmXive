"""
Check for class imbalance in the glass-forming dataset.

This script calculates the ratio of glass to crystalline samples.
If the ratio exceeds 3:1 (either way), it writes a report and aborts
the pipeline to enforce FR-006.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/imbalance_check.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
IMBALANCE_THRESHOLD = 3.0
GLASS_LABEL = 'glass'
CRYSTALLINE_LABEL = 'crystalline'
OUTPUT_REPORT_PATH = 'data/derived/imbalance_report.json'


def load_data(input_path: str) -> pd.DataFrame:
    """Load the dataset from the specified CSV path."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    if 'phase_label' not in df.columns:
        raise ValueError(f"Column 'phase_label' not found in {input_path}. Available columns: {df.columns.tolist()}")
    
    return df


def calculate_imbalance_ratio(df: pd.DataFrame, label_col: str = 'phase_label') -> dict:
    """
    Calculate the count and ratio of glass vs crystalline samples.
    
    Returns a dictionary with counts, total, and the ratio of the majority class to the minority class.
    """
    counts = df[label_col].value_counts()
    total = len(df)
    
    if len(counts) == 0:
        raise ValueError("Dataset is empty or contains no labels.")
    
    # Identify majority and minority classes
    majority_class = counts.idxmax()
    minority_class = counts.idxmin()
    majority_count = counts.max()
    minority_count = counts.min()
    
    if minority_count == 0:
        ratio = float('inf')
    else:
        ratio = majority_count / minority_count
    
    return {
        'total_samples': total,
        'class_counts': counts.to_dict(),
        'majority_class': majority_class,
        'minority_class': minority_class,
        'majority_count': majority_count,
        'minority_count': minority_count,
        'ratio': ratio,
        'ratio_threshold': IMBALANCE_THRESHOLD
    }


def write_report(report_data: dict, output_path: str):
    """Write the imbalance report to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    logger.info(f"Imbalance report written to {output_path}")


def check_imbalance(input_path: str, output_path: str = OUTPUT_REPORT_PATH) -> bool:
    """
    Main logic to check for imbalance.
    
    Returns True if the dataset is suitable (ratio <= threshold).
    Returns False if the dataset is unsuitable (ratio > threshold).
    """
    try:
        df = load_data(input_path)
        stats = calculate_imbalance_ratio(df)
        
        logger.info(f"Imbalance Ratio: {stats['ratio']:.2f} ({stats['majority_class']}:{stats['minority_class']})")
        
        if stats['ratio'] > IMBALANCE_THRESHOLD:
            report = {
                'flag': 'UNSUITABLE_FOR_BINARY_CLASSIFICATION',
                'reason': f'Class imbalance ratio ({stats["ratio"]:.2f}) exceeds threshold ({IMBALANCE_THRESHOLD}).',
                'statistics': stats
            }
            write_report(report, output_path)
            logger.error(f"ABORT: Imbalance ratio {stats['ratio']:.2f} > {IMBALANCE_THRESHOLD}. Pipeline halted.")
            return False
        else:
            report = {
                'flag': 'SUITABLE',
                'reason': f'Class imbalance ratio ({stats["ratio"]:.2f}) is within acceptable limits.',
                'statistics': stats
            }
            write_report(report, output_path)
            logger.info("Pipeline check passed: Class distribution is suitable.")
            return True
            
    except Exception as e:
        logger.critical(f"Critical error during imbalance check: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description='Check dataset for class imbalance.')
    parser.add_argument('--input', type=str, required=True, help='Path to the input CSV file with phase labels.')
    parser.add_argument('--output', type=str, default=OUTPUT_REPORT_PATH, help='Path to write the imbalance report JSON.')
    
    args = parser.parse_args()
    
    if not check_imbalance(args.input, args.output):
        # Exit with error code to abort the pipeline
        sys.exit(1)
    
    sys.exit(0)


if __name__ == '__main__':
    main()