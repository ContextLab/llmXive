"""
Sensitivity analysis for predictive interval calibration.

This module implements a sensitivity analysis loop that sweeps the absolute
deviation between empirical and nominal coverage across a configurable range.
It calculates the count and percentage of series/horizon/model combinations
that fall within each threshold.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import pandas as pd

# Import shared utilities from project modules
# Note: load_config is expected to be in run_pipeline.py or a shared config module
# Based on API surface, we will implement a local load_config or import from run_pipeline if available.
# Since run_pipeline.py has load_config, we can import it if the path is set correctly.
# However, to be safe and self-contained, we'll assume config.yaml is in the root.

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_coverage_results(input_path: str) -> pd.DataFrame:
    """
    Load coverage results from T016/T017.

    Expected columns: series_id, model, horizon, nominal_coverage, empirical_coverage, deviation
    If 'deviation' is not present, it will be calculated.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Coverage results file not found: {input_path}")

    df = pd.read_csv(input_path)

    # Ensure deviation column exists
    if 'deviation' not in df.columns:
        if 'nominal_coverage' in df.columns and 'empirical_coverage' in df.columns:
            df['deviation'] = np.abs(df['nominal_coverage'] - df['empirical_coverage'])
        else:
            raise ValueError("Input file must contain 'nominal_coverage' and 'empirical_coverage' columns or 'deviation' column")

    return df

def run_sensitivity_analysis(
    df: pd.DataFrame,
    sensitivity_range: List[float],
    threshold_step: float = 0.01
) -> pd.DataFrame:
    """
    Perform sensitivity analysis by sweeping thresholds.

    Args:
        df: DataFrame with coverage results including 'deviation' column.
        sensitivity_range: List of [min, max] thresholds from config.
        threshold_step: Step size for linear sweep.

    Returns:
        DataFrame with threshold, count_within_threshold, percentage.
    """
    min_thresh, max_thresh = sensitivity_range
    thresholds = np.arange(min_thresh, max_thresh + threshold_step, threshold_step)

    results = []
    total_count = len(df)

    if total_count == 0:
        logging.warning("Input dataframe is empty. Returning empty results.")
        return pd.DataFrame(columns=['threshold', 'count_within_threshold', 'percentage'])

    for thresh in thresholds:
        count = (df['deviation'] <= thresh).sum()
        percentage = (count / total_count) * 100
        results.append({
            'threshold': round(thresh, 4),
            'count_within_threshold': int(count),
            'percentage': round(percentage, 2)
        })

    return pd.DataFrame(results)

def main():
    """Main entry point for sensitivity analysis."""
    parser = argparse.ArgumentParser(description="Run sensitivity analysis on coverage results.")
    parser.add_argument(
        "--input",
        type=str,
        default="results/coverage.csv",
        help="Path to coverage results CSV (from T019)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/sensitivity_analysis.csv",
        help="Path for output sensitivity analysis CSV"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to configuration file"
    )
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    try:
        # Load configuration
        logger.info(f"Loading configuration from {args.config}")
        config = load_config(args.config)

        if 'sensitivity_range' not in config:
            raise KeyError("sensitivity_range not found in config.yaml")

        sensitivity_range = config['sensitivity_range']
        if not isinstance(sensitivity_range, list) or len(sensitivity_range) != 2:
            raise ValueError("sensitivity_range must be a list of two floats [min, max]")

        logger.info(f"Sensitivity range: {sensitivity_range}")

        # Load coverage results
        # Note: T019 produces results/coverage.csv. T016 produces coverage_intermediate.csv.
        # T017 produces pvalues.json. The final aggregated results are in results/coverage.csv (T019).
        # We need the deviation column which is calculated in T019.
        logger.info(f"Loading coverage results from {args.input}")
        df = load_coverage_results(args.input)

        logger.info(f"Loaded {len(df)} records. Columns: {list(df.columns)}")

        # Run sensitivity analysis
        logger.info("Running sensitivity analysis...")
        sensitivity_df = run_sensitivity_analysis(df, sensitivity_range)

        # Save results
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.exists(output_dir):
            os.makedirs(output_dir)

        sensitivity_df.to_csv(args.output, index=False)
        logger.info(f"Sensitivity analysis results saved to {args.output}")

        # Print summary
        logger.info("Summary:")
        logger.info(sensitivity_df.to_string(index=False))

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except KeyError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
