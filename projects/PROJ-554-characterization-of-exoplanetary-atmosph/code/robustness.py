"""
T026: Compute and report the CI width of the water mixing ratio distribution.

This module calculates the 95% confidence interval width of the water mixing ratio
derived from the retrieval results. It serves as a measure of robustness per SC-003.
The result is reported as a measured outcome, not a pipeline gate (no RuntimeError).
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd

from config import get_config

# Configure logging
logger = logging.getLogger(__name__)

def load_retrieval_results(config: Dict[str, Any]) -> pd.DataFrame:
    """
    Load the retrieval results from the processed data directory.

    Args:
        config: Configuration dictionary containing paths.

    Returns:
        DataFrame containing retrieval results.
    """
    processed_dir = Path(config["paths"]["processed"])
    results_file = processed_dir / "retrieval_results.csv"

    if not results_file.exists():
        raise FileNotFoundError(
            f"Retrieval results file not found: {results_file}. "
            "Please ensure T020 has been completed successfully."
        )

    df = pd.read_csv(results_file)
    logger.info(f"Loaded {len(df)} retrieval results from {results_file}")
    return df

def compute_ci_width(
    df: pd.DataFrame,
    column: str = "water_mixing_ratio",
    ci_level: float = 0.95,
) -> Optional[float]:
    """
    Compute the confidence interval width of the specified column.

    Args:
        df: DataFrame containing the data.
        column: Name of the column to analyze.
        ci_level: Confidence level (default 0.95 for 95% CI).

    Returns:
        The width of the confidence interval (upper - lower), or None if not computable.
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame. Available: {df.columns.tolist()}")

    # Filter out non-numeric and NaN values
    values = df[column].dropna()
    values = values[values.apply(lambda x: isinstance(x, (int, float)))]

    if len(values) < 2:
        logger.warning(f"Insufficient data points ({len(values)}) to compute CI width for '{column}'.")
        return None

    # Compute confidence interval using scipy.stats
    try:
        import scipy.stats as stats
        ci = stats.t.interval(
            ci_level,
            len(values) - 1,
            loc=np.mean(values),
            scale=stats.sem(values),
        )
        width = ci[1] - ci[0]
        logger.info(f"Computed 95% CI width for '{column}': {width:.6f} (CI: [{ci[0]:.6f}, {ci[1]:.6f}])")
        return width
    except Exception as e:
        logger.error(f"Failed to compute CI width: {e}")
        return None

def determine_threshold_met(ci_width: Optional[float], threshold: float = 0.5) -> bool:
    """
    Determine if the CI width meets the robustness threshold.

    Args:
        ci_width: The computed confidence interval width.
        threshold: The maximum acceptable CI width (default 0.5).

    Returns:
        True if the CI width is below the threshold, False otherwise.
    """
    if ci_width is None:
        logger.warning("CI width is None; threshold cannot be evaluated.")
        return False

    met = ci_width <= threshold
    logger.info(f"CI width ({ci_width:.6f}) {'meets' if met else 'exceeds'} threshold ({threshold}).")
    return met

def save_robustness_report(
    config: Dict[str, Any],
    ci_width: Optional[float],
    threshold_met: bool,
    ci_lower: Optional[float] = None,
    ci_upper: Optional[float] = None,
    n_samples: int = 0,
) -> Path:
    """
    Save the robustness report to the results directory.

    Args:
        config: Configuration dictionary containing paths.
        ci_width: The computed confidence interval width.
        threshold_met: Boolean indicating if the threshold was met.
        ci_lower: Lower bound of the CI (optional).
        ci_upper: Upper bound of the CI (optional).
        n_samples: Number of samples used (optional).

    Returns:
        Path to the saved report file.
    """
    results_dir = Path(config["paths"]["results"])
    results_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "ci_width": ci_width,
        "threshold_met": threshold_met,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "n_samples": n_samples,
        "description": "95% CI width of water mixing ratio distribution (SC-003 robustness measure)",
    }

    report_file = results_dir / "robustness_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Saved robustness report to {report_file}")
    return report_file

def main() -> None:
    """
    Main entry point for T026.
    Computes CI width of water mixing ratio and saves the robustness report.
    """
    config = get_config()
    logger.info("Starting T026: Compute CI width of water mixing ratio distribution")

    try:
        # Load retrieval results
        df = load_retrieval_results(config)

        # Compute CI width
        ci_width = compute_ci_width(df, column="water_mixing_ratio", ci_level=0.95)

        # Determine threshold (using a conservative threshold of 0.5 for log10 mixing ratio)
        threshold_met = determine_threshold_met(ci_width, threshold=0.5)

        # Extract CI bounds for reporting
        ci_lower = None
        ci_upper = None
        if ci_width is not None:
            # Recompute bounds for reporting
            import scipy.stats as stats
            values = df["water_mixing_ratio"].dropna()
            values = values[values.apply(lambda x: isinstance(x, (int, float)))]
            if len(values) >= 2:
                ci = stats.t.interval(
                    0.95,
                    len(values) - 1,
                    loc=np.mean(values),
                    scale=stats.sem(values),
                )
                ci_lower, ci_upper = ci

        # Save report
        save_robustness_report(
            config=config,
            ci_width=ci_width,
            threshold_met=threshold_met,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            n_samples=len(df),
        )

        logger.info("T026 completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during T026 execution: {e}")
        raise

if __name__ == "__main__":
    # Setup logging for script execution
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    main()
