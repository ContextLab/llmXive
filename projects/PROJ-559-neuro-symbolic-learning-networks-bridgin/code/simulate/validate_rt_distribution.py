"""
Validate response time distribution for simulation logs.

Checks the 'no consecutive empty bins > 5s' constraint (SC-005) using histogram binning.
Bins are 1s wide. Fails if >2 consecutive empty bins are found.
"""
import os
import sys
import json
import logging
import argparse
import pandas as pd
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BIN_WIDTH = 1.0  # seconds
MAX_CONSECUTIVE_EMPTY = 2
INPUT_FILE = "data/derived/dryrun_logs.csv"
OUTPUT_FILE = "data/derived/rt_distribution_validation.json"

def load_simulation_logs(file_path: str) -> pd.DataFrame:
    """
    Load simulation logs from CSV.

    Args:
        file_path: Path to the CSV file containing simulation logs.

    Returns:
        DataFrame with simulation log records.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Simulation log file not found at: {file_path}")

    logger.info(f"Loading simulation logs from: {file_path}")
    df = pd.read_csv(file_path)

    required_columns = ['rt_seconds', 'student_id', 'problem_id', 'condition']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    logger.info(f"Loaded {len(df)} simulation log records")
    return df

def validate_rt_distribution(df: pd.DataFrame) -> dict:
    """
    Validate the response time distribution against SC-005 constraint.

    Algorithm:
    1. Create histogram bins of 1s width from min to max rt_seconds.
    2. Count empty bins (count == 0).
    3. Check for consecutive runs of empty bins.
    4. Fail if any run exceeds MAX_CONSECUTIVE_EMPTY (2).

    Args:
        df: DataFrame with 'rt_seconds' column.

    Returns:
        Validation result dictionary with pass/fail status and details.
    """
    rt_data = df['rt_seconds'].dropna()

    if len(rt_data) == 0:
        logger.error("No valid response time data found")
        return {
            'passed': False,
            'reason': 'No valid response time data found',
            'consecutive_empty_bins': 0,
            'max_consecutive_allowed': MAX_CONSECUTIVE_EMPTY
        }

    min_rt = rt_data.min()
    max_rt = rt_data.max()

    logger.info(f"Response time range: {min_rt:.2f}s to {max_rt:.2f}s")

    # Create bins
    bins = np.arange(min_rt, max_rt + BIN_WIDTH, BIN_WIDTH)
    if len(bins) < 2:
        logger.warning("Insufficient range for binning, treating as pass")
        return {
            'passed': True,
            'reason': 'Insufficient range for binning',
            'consecutive_empty_bins': 0,
            'max_consecutive_allowed': MAX_CONSECUTIVE_EMPTY,
            'bin_count': 0
        }

    # Calculate histogram
    counts, _ = np.histogram(rt_data, bins=bins)

    # Find empty bins
    empty_bins = counts == 0
    empty_indices = np.where(empty_bins)[0]

    if len(empty_indices) == 0:
        logger.info("No empty bins found. Validation passed.")
        return {
            'passed': True,
            'reason': 'No empty bins found',
            'consecutive_empty_bins': 0,
            'max_consecutive_allowed': MAX_CONSECUTIVE_EMPTY,
            'bin_count': len(counts)
        }

    # Find consecutive runs of empty bins
    max_consecutive = 0
    current_consecutive = 0

    for i in range(len(empty_indices)):
        if i == 0 or empty_indices[i] == empty_indices[i-1] + 1:
            current_consecutive += 1
            max_consecutive = max(max_consecutive, current_consecutive)
        else:
            current_consecutive = 1

    logger.info(f"Maximum consecutive empty bins found: {max_consecutive}")

    passed = max_consecutive <= MAX_CONSECUTIVE_EMPTY

    if passed:
        logger.info(f"Validation PASSED: {max_consecutive} <= {MAX_CONSECUTIVE_EMPTY}")
    else:
        logger.error(f"Validation FAILED: {max_consecutive} > {MAX_CONSECUTIVE_EMPTY}")

    return {
        'passed': passed,
        'reason': f'Max consecutive empty bins: {max_consecutive}' if not passed else 'Distribution is valid',
        'consecutive_empty_bins': max_consecutive,
        'max_consecutive_allowed': MAX_CONSECUTIVE_EMPTY,
        'bin_count': len(counts),
        'total_bins_empty': int(empty_bins.sum())
    }

def save_validation_report(result: dict, output_path: str) -> None:
    """
    Save validation result to JSON file.

    Args:
        result: Validation result dictionary.
        output_path: Path to output JSON file.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Validation report saved to: {output_path}")

def main():
    """Main entry point for response time distribution validation."""
    parser = argparse.ArgumentParser(
        description='Validate response time distribution for simulation logs.'
    )
    parser.add_argument(
        '--input',
        type=str,
        default=INPUT_FILE,
        help=f'Input CSV file path (default: {INPUT_FILE})'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=OUTPUT_FILE,
        help=f'Output JSON file path (default: {OUTPUT_FILE})'
    )

    args = parser.parse_args()

    try:
        # Load data
        df = load_simulation_logs(args.input)

        # Validate distribution
        result = validate_rt_distribution(df)

        # Save report
        save_validation_report(result, args.output)

        # Exit with appropriate code
        if result['passed']:
            logger.info("Validation completed successfully.")
            sys.exit(0)
        else:
            logger.error("Validation failed. Pipeline blocked.")
            sys.exit(1)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()