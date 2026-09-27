"""
Sensitivity Output Module for VAERS Disproportionality Study.

This module handles the generation and formatting of sensitivity analysis output files.
"""

import os
import sys
import logging
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np

from src.utils.config import ensure_dirs

logger = logging.getLogger(__name__)


def load_sensitivity_results(sensitivity_path: str) -> pd.DataFrame:
    """
    Load sensitivity analysis results from CSV.

    Args:
        sensitivity_path: Path to sensitivity_analysis.csv

    Returns:
        DataFrame with sensitivity analysis results
    """
    sensitivity_path = Path(sensitivity_path)
    if not sensitivity_path.exists():
        raise FileNotFoundError(f"Sensitivity results file not found: {sensitivity_path}")

    df = pd.read_csv(sensitivity_path)
    logger.info(f"Loaded {len(df)} sensitivity results from {sensitivity_path}")
    return df


def calculate_deltas_for_top_signals(
    signals_df: pd.DataFrame,
    sensitivity_df: pd.DataFrame,
    top_n: int = 5
) -> pd.DataFrame:
    """
    Calculate and format delta metrics for top N signals.

    Args:
        signals_df: DataFrame with primary analysis signals
        sensitivity_df: DataFrame with sensitivity analysis results
        top_n: Number of top signals to include

    Returns:
        DataFrame with formatted delta metrics
    """
    # Get top N signals from primary analysis
    top_signals = signals_df.head(top_n)

    # Merge with sensitivity results
    merged = top_signals.merge(
        sensitivity_df,
        on='soc',
        how='left',
        suffixes=('_primary', '_sensitivity')
    )

    # Calculate deltas (already computed in sensitivity_df, but verify)
    if 'ror_delta' in merged.columns:
        # Deltas already present
        output_df = merged[['soc', 'ror_delta', 'prr_delta', 'ic_delta', 'baseline_type']].copy()
    else:
        # Calculate deltas from raw metrics
        output_df = pd.DataFrame({
            'soc': merged['soc'],
            'ror_delta': merged['ror_sensitivity'] - merged['ror_primary'],
            'prr_delta': merged['prr_sensitivity'] - merged['prr_primary'],
            'ic_delta': merged['ic_sensitivity'] - merged['ic_primary'],
            'baseline_type': 'flu_only_vs_primary'
        })

    logger.info(f"Calculated deltas for {len(output_df)} top signals")
    return output_df


def generate_sensitivity_delta_csv(
    signals_df: pd.DataFrame,
    sensitivity_df: pd.DataFrame,
    output_path: str,
    top_n: int = 5
) -> pd.DataFrame:
    """
    Generate the sensitivity analysis delta CSV file.

    Args:
        signals_df: DataFrame with primary analysis signals
        sensitivity_df: DataFrame with sensitivity analysis results
        output_path: Path to write output/sensitivity_analysis.csv
        top_n: Number of top signals to include

    Returns:
        DataFrame with delta metrics
    """
    # Calculate deltas for top signals
    result_df = calculate_deltas_for_top_signals(signals_df, sensitivity_df, top_n)

    # Ensure output directory exists
    ensure_dirs()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to CSV
    result_df.to_csv(output_path, index=False)
    logger.info(f"Wrote sensitivity delta CSV to {output_path}")

    return result_df


def main():
    """Main entry point for sensitivity output generation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/sensitivity_output.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger.info("Starting sensitivity output generation (T028)")

    try:
        signals_path = 'output/signals.csv'
        sensitivity_path = 'output/sensitivity_analysis.csv'
        output_path = 'output/sensitivity_deltas.csv'

        # Load inputs
        signals_df = pd.read_csv(signals_path)
        sensitivity_df = pd.read_csv(sensitivity_path)

        # Generate output
        result_df = generate_sensitivity_delta_csv(
            signals_df,
            sensitivity_df,
            output_path
        )

        logger.info(f"Sensitivity output generation complete. Results: {len(result_df)} rows")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Required file not found: {e}")
        logger.error("Ensure T026 (signal generation) and T027 (sensitivity analysis) are complete.")
        return 1
    except Exception as e:
        logger.error(f"Error during sensitivity output generation: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())