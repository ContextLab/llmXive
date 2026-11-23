"""
Power Limitation Check Script for Network Structure Investigation.

This script verifies that the number of predictor variables (network metrics)
does not exceed the number of observations (network instances) by a margin
that would compromise statistical power.

Per task T028, this logic was moved from a standalone runtime check to the
generation phase (T012) to ensure the count is guaranteed at generation time.
This script remains as a validation utility to confirm the condition holds
for the generated dataset.

FR-001 requires at least 50 networks.
The check ensures: observations >= 10 * predictors (Rule of Thumb for PLS/Regression).
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_data(data_path: str) -> pd.DataFrame:
    """
    Load the network metrics CSV.

    Args:
        data_path: Path to the networks CSV file.

    Returns:
        DataFrame containing network metrics.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or has no data rows.
    """
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    df = pd.read_csv(path)

    if df.empty:
        raise ValueError("The loaded dataframe is empty.")

    logger.info(f"Loaded {len(df)} rows from {data_path}")
    return df


def get_predictor_count(df: pd.DataFrame) -> int:
    """
    Count the number of predictor variables (numeric columns used for regression).

    Assumes the first column is an ID and the second is a class label,
    and subsequent numeric columns are metrics.

    Args:
        df: The loaded dataframe.

    Returns:
        Integer count of predictor columns.
    """
    # Heuristic: Exclude 'id' and 'class' columns, count remaining numeric columns
    exclude_cols = {'id', 'class', 'graph_id'}
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Filter out ID-like columns if they are numeric (e.g., if 'id' is int)
    predictors = [col for col in numeric_cols if col.lower() not in exclude_cols]
    
    # Fallback: if no numeric cols found but we have many columns, assume all except id/class
    if not predictors:
        all_cols = df.columns.tolist()
        predictors = [c for c in all_cols if c.lower() not in exclude_cols]

    return len(predictors)


def check_power_limitation(df: pd.DataFrame, threshold_factor: int = 10) -> Dict[str, Any]:
    """
    Check if the number of observations is sufficient for the number of predictors.

    Uses the rule of thumb: Observations >= threshold_factor * Predictors.
    Default threshold_factor is 10 for robust regression/PLS analysis.

    Args:
        df: The dataframe containing the data.
        threshold_factor: The multiplier for the minimum observation count.

    Returns:
        Dictionary with check results:
            - 'passed': bool
            - 'observations': int
            - 'predictors': int
            - 'min_required': int
            - 'message': str
    """
    observations = len(df)
    predictors = get_predictor_count(df)
    min_required = predictors * threshold_factor
    passed = observations >= min_required

    result = {
        "observations": observations,
        "predictors": predictors,
        "min_required": min_required,
        "passed": passed,
        "message": ""
    }

    if passed:
        result["message"] = (
            f"Power check PASSED: {observations} observations >= {min_required} "
            f"(10x {predictors} predictors)."
        )
        logger.info(result["message"])
    else:
        result["message"] = (
            f"Power check FAILED: {observations} observations < {min_required} "
            f"(10x {predictors} predictors). Consider generating more networks."
        )
        logger.warning(result["message"])

    return result


def write_warning_message(result: Dict[str, Any], output_path: Optional[str] = None) -> None:
    """
    Write a warning message to a log file or stdout if the check fails.

    Args:
        result: The result dictionary from check_power_limitation.
        output_path: Optional path to write the warning log.
    """
    if not result["passed"]:
        warning_msg = (
            f"WARNING: Statistical power limitation detected.\n"
            f"Observations: {result['observations']}\n"
            f"Predictors: {result['predictors']}\n"
            f"Minimum required (10x): {result['min_required']}\n"
            f"Recommendation: Increase the number of generated networks."
        )
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(warning_msg)
            logger.info(f"Warning written to {output_path}")
        else:
            logger.warning(warning_msg)
    else:
        logger.info("No power limitation warnings.")


def main():
    """
    Main entry point for the power limitation check script.
    """
    parser = argparse.ArgumentParser(
        description="Check statistical power limitations for network regression analysis."
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        default="data/raw/networks.csv",
        help="Path to the input networks CSV file."
    )
    parser.add_argument(
        "--threshold", "-t",
        type=int,
        default=10,
        help="Minimum observations per predictor ratio (default: 10)."
    )
    parser.add_argument(
        "--output-warning", "-o",
        type=str,
        default=None,
        help="Path to write a warning file if the check fails."
    )

    args = parser.parse_args()

    try:
        logger.info(f"Loading data from {args.input}...")
        df = load_data(args.input)
        
        logger.info("Performing power limitation check...")
        result = check_power_limitation(df, threshold_factor=args.threshold)
        
        write_warning_message(result, args.output_warning)
        
        if not result["passed"]:
            sys.exit(1)
        else:
            sys.exit(0)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(2)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(3)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(4)


if __name__ == "__main__":
    main()