"""
Power Limitation Check Module (Task T028)

Verifies that the generated dataset meets the minimum sample size requirements
mandated by Spec FR-001 (>= 50 samples, 10 per class * 5 classes).
If the requirement is not met, execution halts and a warning is generated.
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_data(csv_path: str) -> Optional[Any]:
    """
    Load the networks CSV file into a pandas DataFrame.
    
    Args:
        csv_path: Path to the networks.csv file.
        
    Returns:
        DataFrame or None if file not found/error.
    """
    try:
        import pandas as pd
        if not os.path.exists(csv_path):
            logger.error(f"Data file not found: {csv_path}")
            return None
        
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} rows from {csv_path}")
        return df
    except Exception as e:
        logger.error(f"Error loading data from {csv_path}: {e}")
        return None

def get_predictor_count(df: Any) -> int:
    """
    Count the total number of samples in the dataset.
    
    Args:
        df: pandas DataFrame containing the network data.
        
    Returns:
        Integer count of rows.
    """
    if df is None:
        return 0
    return len(df)

def check_power_limitation(df: Any, min_samples: int = 50, min_per_class: int = 10) -> Dict[str, Any]:
    """
    Verify the dataset meets power requirements.
    
    Checks:
    1. Total samples >= min_samples (default 50)
    2. Each class has >= min_per_class (default 10) samples
    
    Args:
        df: pandas DataFrame with network data.
        min_samples: Minimum total samples required.
        min_per_class: Minimum samples per class required.
        
    Returns:
        Dictionary with 'passed' (bool), 'total' (int), 'per_class' (dict),
        and 'reason' (str) if failed.
    """
    if df is None:
        return {
            'passed': False,
            'total': 0,
            'per_class': {},
            'reason': "Data is None"
        }

    # Check total count
    total_count = len(df)
    
    # Check per-class count assuming 'class' column exists
    if 'class' not in df.columns:
        return {
            'passed': False,
            'total': total_count,
            'per_class': {},
            'reason': "Column 'class' not found in dataset"
        }
    
    class_counts = df['class'].value_counts().to_dict()
    
    # Identify classes that are under-sampled
    under_sampled_classes = [
        cls for cls, count in class_counts.items() 
        if count < min_per_class
    ]
    
    # Identify if total is under-sampled
    total_under_sampled = total_count < min_samples
    
    if total_under_sampled or under_sampled_classes:
        reason_parts = []
        if total_under_sampled:
            reason_parts.append(f"Total samples ({total_count}) < required ({min_samples})")
        if under_sampled_classes:
            reason_parts.append(f"Classes with insufficient samples: {under_sampled_classes}")
        
        return {
            'passed': False,
            'total': total_count,
            'per_class': class_counts,
            'reason': "; ".join(reason_parts)
        }
    
    return {
        'passed': True,
        'total': total_count,
        'per_class': class_counts,
        'reason': "Power requirement satisfied"
    }

def write_warning_message(output_path: str, result: Dict[str, Any]) -> None:
    """
    Write a specific warning message to the output file if power check fails.
    
    Args:
        output_path: Path to the warning text file.
        result: Dictionary containing the check results.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write("POWER LIMITATION WARNING\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Status: FAILED\n")
        f.write(f"Reason: {result['reason']}\n\n")
        f.write(f"Total Samples: {result['total']}\n")
        f.write(f"Required Total: 50\n\n")
        f.write("Sample Distribution per Class:\n")
        for cls, count in result['per_class'].items():
            f.write(f"  - {cls}: {count}\n")
        f.write("\n")
        f.write("ACTION REQUIRED: \n")
        f.write("The dataset does not meet the minimum power requirements defined in Spec FR-001.\n")
        f.write("Simulation tasks (T021b) must be HALTED until sufficient data is generated.\n")
        f.write("Please re-run data generation (T012) ensuring at least 10 samples per class.\n")
    
    logger.info(f"Warning message written to {output_path}")

def main():
    """
    Main entry point for the power limitation check.
    """
    parser = argparse.ArgumentParser(description="Check power limitation for network dataset")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/raw/networks.csv",
        help="Path to the input networks CSV file"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/analysis/power_warning.txt",
        help="Path to the output warning file (if check fails)"
    )
    parser.add_argument(
        "--min-samples", 
        type=int, 
        default=50,
        help="Minimum total samples required"
    )
    parser.add_argument(
        "--min-per-class", 
        type=int, 
        default=10,
        help="Minimum samples per class required"
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting power limitation check for {args.input}")
    
    # Load data
    df = load_data(args.input)
    
    if df is None:
        logger.error("Failed to load data. Halting execution.")
        sys.exit(1)
    
    # Perform check
    result = check_power_limitation(df, args.min_samples, args.min_per_class)
    
    if not result['passed']:
        logger.warning("Power limitation check FAILED.")
        logger.warning(f"Reason: {result['reason']}")
        
        # Write warning file
        write_warning_message(args.output, result)
        
        # HALT EXECUTION
        logger.error("HALTING EXECUTION: Insufficient data power.")
        sys.exit(1)
    else:
        logger.info("Power limitation check PASSED.")
        logger.info(f"Total samples: {result['total']}")
        logger.info(f"Distribution: {result['per_class']}")
        sys.exit(0)

if __name__ == "__main__":
    main()
