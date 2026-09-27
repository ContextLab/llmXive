"""
Sensitivity Analysis Module for VAERS Disproportionality Study.

This module implements sensitivity analysis comparing the Non-COVID (all other vaccines)
baseline vs Flu-only baseline for top signals identified in the primary analysis.
"""

import os
import sys
import logging
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np

# Import from existing API surface
from src.analysis.disproportionality import (
    calculate_ror,
    calculate_prr,
    calculate_ic,
    calculate_ci_ror,
    calculate_ci_prr,
    calculate_ci_ic,
    apply_continuity_correction,
)
from src.utils.config import ensure_dirs

# Setup logging
logger = logging.getLogger(__name__)

# Constants
MIN_REPORTS = 5
CONTINUITY_CORRECTION = 0.5


def load_signals(signals_path: str) -> pd.DataFrame:
    """
    Load the signals CSV generated from the primary analysis.

    Args:
        signals_path: Path to output/signals.csv

    Returns:
        DataFrame with signal metrics

    Raises:
        FileNotFoundError: If the signals file does not exist
        ValueError: If the file is empty or has incorrect schema
    """
    signals_path = Path(signals_path)
    if not signals_path.exists():
        raise FileNotFoundError(f"Signals file not found: {signals_path}")

    df = pd.read_csv(signals_path)

    # Validate required columns
    required_cols = ['soc', 'ror', 'ror_ci_lower', 'ror_ci_upper',
                    'prr', 'prr_ci_lower', 'prr_ci_upper',
                    'ic', 'ic_ci_lower', 'ic_ci_upper', 'signal_flag']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Signals file missing required columns: {missing_cols}")

    # Filter to only signals (signal_flag == True)
    signals_df = df[df['signal_flag'] == True].copy()

    if len(signals_df) == 0:
        logger.warning("No signals found in signals.csv. Sensitivity analysis will produce empty output.")
        return signals_df

    logger.info(f"Loaded {len(signals_df)} signals from {signals_path}")
    return signals_df


def load_cleaned_data(cleaned_data_path: str) -> pd.DataFrame:
    """
    Load the cleaned VAERS dataset.

    Args:
        cleaned_data_path: Path to data/processed/cleaned_vaers.parquet

    Returns:
        DataFrame with cleaned VAERS data

    Raises:
        FileNotFoundError: If the cleaned data file does not exist
    """
    cleaned_data_path = Path(cleaned_data_path)
    if not cleaned_data_path.exists():
        raise FileNotFoundError(f"Cleaned data file not found: {cleaned_data_path}")

    if cleaned_data_path.suffix == '.parquet':
        df = pd.read_parquet(cleaned_data_path)
    else:
        df = pd.read_csv(cleaned_data_path)

    logger.info(f"Loaded {len(df)} rows from {cleaned_data_path}")
    return df


def filter_data_for_baseline(df: pd.DataFrame, baseline_type: str) -> pd.DataFrame:
    """
    Filter the cleaned data for a specific baseline group.

    Args:
        df: Cleaned VAERS dataframe
        baseline_type: Either 'primary' (Non-COVID, Non-Flu) or 'flu_only' (Flu-only)

    Returns:
        Filtered DataFrame containing only the specified baseline group and COVID-19 cases
    """
    if baseline_type == 'primary':
        # Primary Baseline: Non-COVID, Non-Flu
        # Keep COVID-19 cases and Non-COVID, Non-Flu cases
        mask = (df['VAX_TYPE'] == 'COVID-19') | \
               ((df['VAX_TYPE'] != 'COVID-19') & (df['VAX_TYPE'].str.contains('Influenza', case=False, na=False) == False))
        filtered_df = df[mask].copy()
        logger.info(f"Filtered for primary baseline: {len(filtered_df)} rows")

    elif baseline_type == 'flu_only':
        # Flu-only Baseline: Keep COVID-19 cases and Flu-only cases
        mask = (df['VAX_TYPE'] == 'COVID-19') | \
               (df['VAX_TYPE'].str.contains('Influenza', case=False, na=False))
        filtered_df = df[mask].copy()
        logger.info(f"Filtered for flu-only baseline: {len(filtered_df)} rows")

    else:
        raise ValueError(f"Unknown baseline_type: {baseline_type}. Must be 'primary' or 'flu_only'")

    return filtered_df


def calculate_metrics_for_soc(
    df: pd.DataFrame,
    soc_code: str,
    event_col: str = 'SOC'
) -> Dict[str, float]:
    """
    Calculate ROR, PRR, IC and their confidence intervals for a specific SOC.

    Args:
        df: Filtered DataFrame containing COVID-19 and baseline cases
        soc_code: The SOC code to analyze
        event_col: Column name containing SOC codes

    Returns:
        Dictionary with ROR, PRR, IC and their 95% CIs, or None if insufficient data
    """
    # Build 2x2 contingency table
    # Rows: Event (SOC matches) vs No Event
    # Cols: COVID-19 vs Baseline (Non-COVID)

    # Count events for this SOC in COVID-19 group
    covid_events = len(df[(df['VAX_TYPE'] == 'COVID-19') & (df[event_col] == soc_code)])
    # Count total COVID-19 cases
    covid_total = len(df[df['VAX_TYPE'] == 'COVID-19'])
    covid_no_event = covid_total - covid_events

    # Count events for this SOC in baseline group
    baseline_events = len(df[(df['VAX_TYPE'] != 'COVID-19') & (df[event_col] == soc_code)])
    # Count total baseline cases
    baseline_total = len(df[df['VAX_TYPE'] != 'COVID-19'])
    baseline_no_event = baseline_total - baseline_events

    # Check minimum report requirement
    total_reports = covid_events + baseline_events
    if total_reports < MIN_REPORTS:
        logger.debug(f"SOC {soc_code}: Insufficient reports ({total_reports} < {MIN_REPORTS})")
        return None

    # Apply continuity correction
    a, b, c, d = apply_continuity_correction(
        covid_events, covid_no_event, baseline_events, baseline_no_event
    )

    # Calculate metrics
    ror = calculate_ror(a, b, c, d)
    ror_ci_lower, ror_ci_upper = calculate_ci_ror(a, b, c, d)

    prr = calculate_prr(a, b, c, d)
    prr_ci_lower, prr_ci_upper = calculate_ci_prr(a, b, c, d)

    ic = calculate_ic(a, b, c, d)
    ic_ci_lower, ic_ci_upper = calculate_ci_ic(a, b, c, d)

    return {
        'ror': ror,
        'ror_ci_lower': ror_ci_lower,
        'ror_ci_upper': ror_ci_upper,
        'prr': prr,
        'prr_ci_lower': prr_ci_lower,
        'prr_ci_upper': prr_ci_upper,
        'ic': ic,
        'ic_ci_lower': ic_ci_lower,
        'ic_ci_upper': ic_ci_upper,
        'covid_events': covid_events,
        'baseline_events': baseline_events,
        'total_reports': total_reports
    }


def run_sensitivity_analysis(
    signals_df: pd.DataFrame,
    cleaned_df: pd.DataFrame,
    output_path: str
) -> pd.DataFrame:
    """
    Run sensitivity analysis comparing primary baseline vs flu-only baseline.

    Args:
        signals_df: DataFrame with top signals from primary analysis
        cleaned_df: Full cleaned VAERS dataset
        output_path: Path to write output/sensitivity_analysis.csv

    Returns:
        DataFrame with sensitivity analysis results
    """
    results = []

    # Get top 5 signals (or all if fewer than 5)
    top_signals = signals_df.head(5)

    if len(top_signals) == 0:
        logger.warning("No signals to analyze. Creating empty output file.")
        # Create empty DataFrame with correct schema
        output_df = pd.DataFrame(columns=[
            'soc', 'ror_delta', 'prr_delta', 'ic_delta', 'baseline_type'
        ])
        output_df.to_csv(output_path, index=False)
        return output_df

    logger.info(f"Analyzing top {len(top_signals)} signals for sensitivity")

    for idx, row in top_signals.iterrows():
        soc_code = row['soc']
        primary_metrics = row.to_dict()

        # Calculate metrics for primary baseline (already in signals_df)
        primary_ror = primary_metrics['ror']
        primary_prr = primary_metrics['prr']
        primary_ic = primary_metrics['ic']

        # Filter data for flu-only baseline
        flu_df = filter_data_for_baseline(cleaned_df, 'flu_only')

        # Calculate metrics for flu-only baseline
        flu_metrics = calculate_metrics_for_soc(flu_df, soc_code)

        if flu_metrics is None:
            logger.warning(f"SOC {soc_code}: Insufficient data for flu-only baseline. Skipping.")
            continue

        flu_ror = flu_metrics['ror']
        flu_prr = flu_metrics['prr']
        flu_ic = flu_metrics['ic']

        # Calculate deltas (Flu-only - Primary)
        ror_delta = flu_ror - primary_ror
        prr_delta = flu_prr - primary_prr
        ic_delta = flu_ic - primary_ic

        results.append({
            'soc': soc_code,
            'ror_delta': ror_delta,
            'prr_delta': prr_delta,
            'ic_delta': ic_delta,
            'baseline_type': 'flu_only_vs_primary'
        })

        logger.info(f"SOC {soc_code}: ROR delta={ror_delta:.4f}, PRR delta={prr_delta:.4f}, IC delta={ic_delta:.4f}")

    # Create output DataFrame
    output_df = pd.DataFrame(results)

    # Ensure output directory exists
    ensure_dirs()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to CSV
    output_df.to_csv(output_path, index=False)
    logger.info(f"Wrote sensitivity analysis results to {output_path}")

    return output_df


def main():
    """Main entry point for sensitivity analysis."""
    # Setup logging
    log_path = Path('logs/sensitivity.log')
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger.info("Starting sensitivity analysis (T027)")

    try:
        # Define paths
        signals_path = 'output/signals.csv'
        cleaned_data_path = 'data/processed/cleaned_vaers.parquet'
        output_path = 'output/sensitivity_analysis.csv'

        # Load inputs
        logger.info("Loading signals from primary analysis...")
        signals_df = load_signals(signals_path)

        logger.info("Loading cleaned VAERS data...")
        cleaned_df = load_cleaned_data(cleaned_data_path)

        # Run analysis
        logger.info("Running sensitivity analysis...")
        result_df = run_sensitivity_analysis(signals_df, cleaned_df, output_path)

        logger.info(f"Sensitivity analysis complete. Results written to {output_path}")
        logger.info(f"Analyzed {len(result_df)} signals")

        # Print summary
        if len(result_df) > 0:
            logger.info("Summary of deltas:")
            logger.info(result_df[['soc', 'ror_delta', 'prr_delta', 'ic_delta']].to_string())

        return 0

    except FileNotFoundError as e:
        logger.error(f"Required file not found: {e}")
        logger.error("Ensure T026 (signal generation) and T015 (data cleaning) are complete.")
        return 1
    except Exception as e:
        logger.error(f"Error during sensitivity analysis: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
