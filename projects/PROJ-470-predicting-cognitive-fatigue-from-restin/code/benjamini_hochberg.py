"""Benjamini-Hochberg correction for multiple comparisons.

This module implements the Benjamini-Hochberg procedure to control the False
Discovery Rate (FDR) across multiple hypothesis tests (electrodes).

It reads raw correlation results from `data/analysis/raw_correlation_results.csv`,
applies the BH correction using `statsmodels`, and writes the corrected p-values
to `data/analysis/bh_corrected_pvalues.csv`.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

import pandas as pd
from statsmodels.stats.multitest import multipletests

# Ensure we can import from the project root if run as a script
# The API surface expects this module to be importable as `from benjamini_hochberg import ...`
# When run as a script, it should work from the project root or `code/` directory.

def load_config(config_path: str = "code/config.yaml") -> dict:
    """Load configuration from YAML file."""
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logger(name: str, log_file: str | None = None) -> logging.Logger:
    """Set up a logger for this module.

    Args:
        name: Logger name.
        log_file: Optional file path to log to.

    Returns:
        Configured logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if called multiple times
    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Console handler
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File handler if specified
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

    return logger

def load_raw_correlation_results(input_path: str) -> pd.DataFrame:
    """Load the raw correlation results.

    Args:
        input_path: Path to the raw correlation CSV file.

    Returns:
        DataFrame with correlation results.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Raw correlation results not found: {input_path}")

    df = pd.read_csv(input_path)

    required_cols = ['electrode', 'p_value', 'correlation_type']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {input_path}: {missing}")

    return df

def run_benjamini_hochberg(
    df: pd.DataFrame,
    alpha: float = 0.05,
    method: str = 'fdr_bh'
) -> pd.DataFrame:
    """Apply Benjamini-Hochberg correction to p-values.

    Args:
        df: DataFrame containing raw p-values.
        alpha: Significance level (default 0.05).
        method: Method for multiple testing correction (default 'fdr_bh').

    Returns:
        DataFrame with added corrected p-values and significance flags.
    """
    # Extract p-values
    p_values = df['p_value'].values

    # Apply BH correction
    # multipletests returns: (reject, p_corrected, p_corrected_sidak, p_corrected_bonferroni)
    reject, p_corrected, _, _ = multipletests(
        p_values,
        alpha=alpha,
        method=method,
        returnsorted=False
    )

    # Create result DataFrame
    result_df = df.copy()
    result_df['p_corrected'] = p_corrected
    result_df['is_significant'] = reject

    return result_df

def save_corrected_results(df: pd.DataFrame, output_path: str) -> None:
    """Save the corrected results to CSV.

    Args:
        df: DataFrame with corrected results.
        output_path: Path to save the CSV file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)

def main() -> int:
    """Main entry point for Benjamini-Hochberg correction."""
    parser = argparse.ArgumentParser(
        description="Apply Benjamini-Hochberg correction to correlation p-values."
    )
    parser.add_argument(
        '--input',
        type=str,
        default='data/analysis/raw_correlation_results.csv',
        help='Path to raw correlation results CSV'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/analysis/bh_corrected_pvalues.csv',
        help='Path to output corrected p-values CSV'
    )
    parser.add_argument(
        '--alpha',
        type=float,
        default=0.05,
        help='Significance level for FDR control'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='code/config.yaml',
        help='Path to config file'
    )
    parser.add_argument(
        '--log-file',
        type=str,
        default=None,
        help='Path to log file'
    )

    args = parser.parse_args()

    # Setup logger
    logger = setup_logger('benjamini_hochberg', args.log_file)
    logger.info("Starting Benjamini-Hochberg correction.")

    # Load config (for alpha if not overridden)
    try:
        config = load_config(args.config)
        alpha = config.get('fdr_alpha', args.alpha)
    except Exception as e:
        logger.warning(f"Could not load config: {e}. Using default alpha.")
        alpha = args.alpha

    logger.info(f"Using alpha={alpha}")

    # Load raw results
    try:
        raw_df = load_raw_correlation_results(args.input)
        logger.info(f"Loaded {len(raw_df)} raw correlation results from {args.input}")
    except (FileNotFoundError, ValueError) as e:
        logger.error(str(e))
        return 1

    # Run correction
    corrected_df = run_benjamini_hochberg(raw_df, alpha=alpha)

    # Save results
    try:
        save_corrected_results(corrected_df, args.output)
        logger.info(f"Saved corrected results to {args.output}")
        logger.info(f"Significant electrodes (p < {alpha}): {corrected_df['is_significant'].sum()}")
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        return 1

    logger.info("Benjamini-Hochberg correction completed successfully.")
    return 0

if __name__ == '__main__':
    sys.exit(main())
