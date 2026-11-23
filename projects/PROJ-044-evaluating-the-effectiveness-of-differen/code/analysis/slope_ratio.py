"""
Implementation of T036: Slope Ratio Calculation for SC-004.

This module calculates the slope of the accuracy vs. epsilon curve for
alpha=0.1 and alpha=1.0, then verifies if the alpha=0.1 slope is >= 2x
steeper (more negative) than the alpha=1.0 slope.

Dependency: T025 results (sensitivity analysis data).
Output: results/slope_ratio_validation.md
"""
import logging
import sys
from pathlib import Path
from typing import Dict, Tuple, List, Optional

import numpy as np
import pandas as pd

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.stats import load_filtered_data

logger = logging.getLogger(__name__)

def calculate_slope(x: np.ndarray, y: np.ndarray) -> float:
    """
    Calculate the slope of a linear regression line (y = mx + c).
    Returns the slope 'm'.
    """
    if len(x) < 2:
        raise ValueError("Need at least 2 points to calculate slope.")

    # Use numpy's polyfit for linear regression (degree 1)
    # Returns [slope, intercept]
    slope, _ = np.polyfit(x, y, 1)
    return float(slope)

def get_accuracy_for_epsilon(
    df: pd.DataFrame, epsilon: float, alpha: float
) -> Optional[float]:
    """
    Retrieve the average global accuracy for a specific epsilon and alpha.
    Returns None if no data found.
    """
    subset = df[
        (np.isclose(df['epsilon'], epsilon)) & (np.isclose(df['alpha'], alpha))
    ]

    if subset.empty:
        return None

    # Average across seeds for this configuration
    return float(subset['global_accuracy'].mean())

def calculate_slope_ratio_validation(
    df: pd.DataFrame,
    epsilon_values: List[float],
    alpha_low: float = 0.1,
    alpha_high: float = 1.0,
) -> Dict:
    """
    Calculate slopes for alpha=0.1 and alpha=1.0 and validate the ratio.

    Returns a dictionary with:
      - slope_alpha_low: Slope for alpha=0.1
      - slope_alpha_high: Slope for alpha=1.0
      - ratio: |slope_low| / |slope_high|
      - pass_status: True if |slope_low| >= 2 * |slope_high|
      - details: Human-readable explanation
    """
    logger.info(f"Calculating slopes for alpha={alpha_low} and alpha={alpha_high}")

    # Prepare data for regression
    x_low, y_low = [], []
    x_high, y_high = [], []

    for eps in epsilon_values:
        acc_low = get_accuracy_for_epsilon(df, eps, alpha_low)
        acc_high = get_accuracy_for_epsilon(df, eps, alpha_high)

        if acc_low is not None:
            x_low.append(eps)
            y_low.append(acc_low)
        else:
            logger.warning(f"No data for alpha={alpha_low}, epsilon={eps}")

        if acc_high is not None:
            x_high.append(eps)
            y_high.append(acc_high)
        else:
            logger.warning(f"No data for alpha={alpha_high}, epsilon={eps}")

    if len(x_low) < 2:
        raise ValueError(
            f"Insufficient data points for alpha={alpha_low}. "
            f"Found {len(x_low)} points. Need at least 2."
        )
    if len(x_high) < 2:
        raise ValueError(
            f"Insufficient data points for alpha={alpha_high}. "
            f"Found {len(x_high)} points. Need at least 2."
        )

    slope_low = calculate_slope(np.array(x_low), np.array(y_low))
    slope_high = calculate_slope(np.array(x_high), np.array(y_high))

    logger.info(f"Slope for alpha={alpha_low}: {slope_low:.6f}")
    logger.info(f"Slope for alpha={alpha_high}: {slope_high:.6f}")

    # SC-004: Verify slope for alpha=0.1 is >= 2x steeper (more negative) than alpha=1.0
    # Steeper means more negative. We compare magnitudes.
    # Condition: |slope_low| >= 2 * |slope_high|
    # Since slopes are expected to be negative (accuracy drops as epsilon drops/noise increases),
    # we compare absolute values.
    
    # Handle edge case where slope_high is 0 or near zero
    if abs(slope_high) < 1e-9:
        if abs(slope_low) > 1e-9:
            ratio = float('inf')
            pass_status = True
            details = "Slope for alpha=1.0 is effectively zero, while alpha=0.1 shows sensitivity. Condition met."
        else:
            ratio = 1.0
            pass_status = False
            details = "Both slopes are effectively zero. Condition not met."
    else:
        ratio = abs(slope_low) / abs(slope_high)
        pass_status = ratio >= 2.0
        details = f"Ratio of |slope_low| / |slope_high| is {ratio:.2f}. " \
                  f"{'Pass' if pass_status else 'Fail'}: Required >= 2.0."

    return {
        "slope_alpha_low": slope_low,
        "slope_alpha_high": slope_high,
        "ratio": ratio,
        "pass_status": pass_status,
        "details": details,
        "alpha_low": alpha_low,
        "alpha_high": alpha_high,
        "epsilon_values_used": epsilon_values
    }

def generate_validation_report(results: Dict, output_path: Path) -> None:
    """
    Generate the slope_ratio_validation.md report.
    """
    report_lines = [
        "# Slope Ratio Validation Report (SC-004)",
        "",
        "## Objective",
        "Verify that the slope of the accuracy vs. epsilon curve for alpha=0.1 is at least",
        "2x steeper (more negative) than the slope for alpha=1.0.",
        "",
        "## Results",
        "",
        f"- **Alpha (Low)**: {results['alpha_low']}",
        f"- **Alpha (High)**: {results['alpha_high']}",
        f"- **Slope (Alpha={results['alpha_low']})**: {results['slope_alpha_low']:.6f}",
        f"- **Slope (Alpha={results['alpha_high']})**: {results['slope_alpha_high']:.6f}",
        f"- **Ratio (|Slope Low| / |Slope High|)**: {results['ratio']:.2f}",
        "",
        "## Validation Status",
        "",
        f"**Status**: {'PASS' if results['pass_status'] else 'FAIL'}",
        "",
        f"**Details**: {results['details']}",
        "",
        "## Configuration Details",
        "",
        f"- **Epsilon values used**: {results['epsilon_values_used']}",
        "",
        "---",
        "Generated by T036: Slope Ratio Calculation.",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    logger.info(f"Validation report written to {output_path}")

def main():
    """
    Entry point for T036.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Define paths
    project_root = Path(__file__).parent.parent.parent
    results_dir = project_root / "results"
    input_file = results_dir / "filtered_data.csv"
    output_file = results_dir / "slope_ratio_validation.md"

    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Ensure T035 (Filter Utility Collapse) has completed and produced results/filtered_data.csv")
        sys.exit(1)

    logger.info(f"Loading filtered data from {input_file}")
    try:
        df = load_filtered_data(input_file)
    except Exception as e:
        logger.error(f"Failed to load filtered data: {e}")
        sys.exit(1)

    # Define epsilon values to analyze (should match the experiment configuration)
    # We infer unique epsilon values from the data for alpha=0.1 to ensure coverage
    alpha_low = 0.1
    alpha_high = 1.0

    # Get unique epsilon values present in the dataset for alpha=0.1
    epsilon_subset = df[df['alpha'] == alpha_low]['epsilon'].unique()
    if len(epsilon_subset) < 2:
        logger.error(f"Insufficient epsilon values for alpha={alpha_low} in data.")
        logger.error("Expected at least 2 distinct epsilon values to calculate a slope.")
        sys.exit(1)
    
    # Sort epsilon values to ensure consistent ordering for regression
    epsilon_values = sorted(epsilon_subset.tolist())
    logger.info(f"Using epsilon values: {epsilon_values}")

    try:
        results = calculate_slope_ratio_validation(
            df, 
            epsilon_values, 
            alpha_low=alpha_low, 
            alpha_high=alpha_high
        )
    except ValueError as e:
        logger.error(f"Calculation failed: {e}")
        sys.exit(1)

    generate_validation_report(results, output_file)

    if results['pass_status']:
        logger.info("Validation PASSED: SC-004 condition met.")
        sys.exit(0)
    else:
        logger.warning("Validation FAILED: SC-004 condition not met.")
        sys.exit(0) # Exit 0 to allow pipeline to continue, but log warning

if __name__ == "__main__":
    main()
