"""
Statistical Significance Module for T017.

Implements hypothesis testing for prediction interval calibration deviations
and applies Benjamini-Hochberg FDR correction across all model-horizon pairs.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Any

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

logger = logging.getLogger(__name__)


def load_coverage_results(input_path: str) -> pd.DataFrame:
    """
    Load coverage results from T016 intermediate output.

    Args:
        input_path: Path to coverage_intermediate.csv

    Returns:
        DataFrame with columns: series_id, model, horizon, empirical_coverage
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)
    required_cols = {"series_id", "model", "horizon", "empirical_coverage"}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Missing required columns: {missing}")

    return df


def load_nominal_levels(config_path: str = "config.yaml") -> Dict[str, float]:
    """
    Load nominal coverage levels from config.yaml.

    Args:
        config_path: Path to config.yaml

    Returns:
        Dictionary mapping model names (or 'all') to nominal levels
    """
    import yaml

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # nominal_levels is a list of floats in config.yaml
    return config.get("nominal_levels", [0.80, 0.95])


def calculate_deviations(
    df: pd.DataFrame, nominal_level: float
) -> pd.DataFrame:
    """
    Calculate deviation between empirical and nominal coverage.

    Args:
        df: Coverage results DataFrame
        nominal_level: The nominal coverage level (e.g., 0.95)

    Returns:
        DataFrame with added 'deviation' column
    """
    df = df.copy()
    df["nominal_coverage"] = nominal_level
    df["deviation"] = df["empirical_coverage"] - nominal_level
    return df


def perform_hypothesis_tests(
    df: pd.DataFrame,
    nominal_levels: List[float],
) -> pd.DataFrame:
    """
    Perform hypothesis tests for each (model, horizon, nominal_level) combination.

    Null hypothesis: The mean deviation is zero (calibrated).
    Alternative: The mean deviation is not zero (miscalibrated).

    Uses a one-sample t-test against zero for the deviations.

    Args:
        df: Coverage results with 'deviation' column
        nominal_levels: List of nominal coverage levels to test

    Returns:
        DataFrame with raw p-values for each test
    """
    results = []

    for nominal in nominal_levels:
        # Filter for this nominal level
        subset = df[df["nominal_coverage"] == nominal]

        if subset.empty:
            logger.warning(f"No data for nominal level {nominal}")
            continue

        # Group by model and horizon
        grouped = subset.groupby(["model", "horizon"])

        for (model, horizon), group in grouped:
            deviations = group["deviation"].values

            if len(deviations) < 2:
                # Not enough samples for t-test
                p_raw = np.nan
                logger.warning(
                    f"Insufficient samples for {model}/{horizon}/{nominal}: "
                    f"n={len(deviations)}"
                )
            else:
                # One-sample t-test against 0 (null: mean deviation = 0)
                _, p_raw = stats.ttest_1samp(deviations, 0.0)

            results.append(
                {
                    "model": model,
                    "horizon": int(horizon),
                    "nominal_coverage": nominal,
                    "n_series": len(deviations),
                    "mean_deviation": float(np.mean(deviations)),
                    "p_raw": float(p_raw),
                }
            )

    return pd.DataFrame(results)


def apply_benjamini_hochberg(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg FDR correction to raw p-values.

    Correction is applied across ALL models × horizons × nominal_levels combined.

    Args:
        df: DataFrame with 'p_raw' column

    Returns:
        DataFrame with added 'p_value' (FDR-corrected) column
    """
    if df.empty:
        logger.warning("Empty input DataFrame for BH correction")
        return df

    p_raw_values = df["p_raw"].values

    # Handle NaN values: multipletests will return NaN for NaN inputs
    # We pass all values at once to correct across the entire set
    reject, p_corr, _, _ = multipletests(
        p_raw_values, method="fdr_bh", alpha=0.05
    )

    df = df.copy()
    df["p_value"] = p_corr
    df["rejected"] = reject

    logger.info(
        f"BH correction applied: {reject.sum()} of {len(reject)} tests rejected "
        f"at alpha=0.05"
    )

    return df


def generate_pvalues_report(
    input_path: str,
    output_path: str,
    config_path: str = "config.yaml",
) -> None:
    """
    Main pipeline to generate statistical significance results.

    1. Load coverage results from T016
    2. Calculate deviations for each nominal level
    3. Perform hypothesis tests for each (model, horizon, nominal)
    4. Apply Benjamini-Hochberg FDR correction across all tests
    5. Save results to JSON

    Args:
        input_path: Path to coverage_intermediate.csv
        output_path: Path for output pvalues.json
        config_path: Path to config.yaml
    """
    logger.info(f"Loading coverage results from {input_path}")
    coverage_df = load_coverage_results(input_path)

    logger.info("Loading nominal levels from config")
    nominal_levels = load_nominal_levels(config_path)

    logger.info(f"Performing hypothesis tests for nominal levels: {nominal_levels}")
    test_results = perform_hypothesis_tests(coverage_df, nominal_levels)

    logger.info("Applying Benjamini-Hochberg FDR correction")
    corrected_results = apply_benjamini_hochberg(test_results)

    # Prepare output: flatten to list of dicts for JSON serialization
    output_data = corrected_results.to_dict(orient="records")

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write to JSON
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Saved p-values to {output_path}")
    logger.info(f"Total tests performed: {len(output_data)}")
    logger.info(
        f"Tests rejected at FDR=0.05: "
        f"{sum(1 for r in output_data if r.get('rejected', False))}"
    )


def main() -> None:
    """Entry point for command-line execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate statistical significance p-values for coverage deviations"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="results/coverage_intermediate.csv",
        help="Path to coverage intermediate results",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/pvalues.json",
        help="Path for output p-values JSON",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to config.yaml",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    generate_pvalues_report(
        input_path=args.input,
        output_path=args.output,
        config_path=args.config,
    )


if __name__ == "__main__":
    main()
