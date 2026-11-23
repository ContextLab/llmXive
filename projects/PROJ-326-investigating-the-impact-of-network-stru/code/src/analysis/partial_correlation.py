"""
Partial Correlation Analysis Module.

Isolates the effect of individual network metrics on diffusion rates
while controlling for confounding variables (e.g., average path length).
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


class PartialCorrelationError(Exception):
    """Custom exception for partial correlation errors."""
    pass


def load_simulation_data() -> pd.DataFrame:
    """
    Loads simulation results from the standard output file.

    Returns:
        pd.DataFrame: The loaded simulation data.

    Raises:
        PartialCorrelationError: If the file is missing or invalid.
    """
    file_path = Path("data/analysis/simulation_results.json")
    if not file_path.exists():
        raise PartialCorrelationError(f"Input file not found: {file_path}")

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise PartialCorrelationError(f"Failed to parse JSON: {e}")

    df = pd.DataFrame(data)

    required_cols = ['diffusion_rate', 'clustering_coefficient', 'average_path_length']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise PartialCorrelationError(f"Missing required columns in simulation data: {missing}")

    # Drop rows with NaN in key columns
    initial_count = len(df)
    df = df.dropna(subset=required_cols)
    dropped = initial_count - len(df)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} rows with NaN values in key columns.")

    if len(df) < 3:
        raise PartialCorrelationError("Insufficient data points for partial correlation (need >= 3).")

    return df


def calculate_partial_correlation(
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray
) -> Tuple[float, float]:
    """
    Calculates the partial correlation between x and y, controlling for z.

    Uses the standard formula: r_xy.z = (r_xy - r_xz * r_yz) / sqrt((1-r_xz^2)(1-r_yz^2))

    Args:
        x: Array of values for variable X.
        y: Array of values for variable Y.
        z: Array of values for control variable Z.

    Returns:
        Tuple[float, float]: (correlation_coefficient, p_value)
    """
    # Ensure inputs are 1D arrays
    x = np.asarray(x).flatten()
    y = np.asarray(y).flatten()
    z = np.asarray(z).flatten()

    if len(x) != len(y) or len(x) != len(z):
        raise PartialCorrelationError("Input arrays must have the same length.")

    if len(x) < 3:
        raise PartialCorrelationError("Need at least 3 data points to calculate correlation.")

    # Calculate pairwise Pearson correlations
    r_xy, p_xy = stats.pearsonr(x, y)
    r_xz, p_xz = stats.pearsonr(x, z)
    r_yz, p_yz = stats.pearsonr(y, z)

    # Partial correlation formula
    numerator = r_xy - (r_xz * r_yz)
    denominator = np.sqrt((1 - r_xz**2) * (1 - r_yz**2))

    if denominator == 0:
        # If denominator is 0, it implies perfect collinearity or variance issues
        # Return 0 correlation with a warning or handle as NaN
        logger.warning("Denominator is zero in partial correlation calculation. Returning NaN.")
        return np.nan, np.nan

    r_partial = numerator / denominator

    # Calculate p-value for partial correlation
    # t = r * sqrt((n - 2 - k) / (1 - r^2)) where k is number of control variables (1 here)
    n = len(x)
    k = 1
    df = n - 2 - k

    if np.abs(r_partial) >= 1.0:
        # Perfect correlation
        p_value = 0.0
    else:
        t_stat = r_partial * np.sqrt(df / (1 - r_partial**2))
        p_value = 2 * (1 - stats.t.cdf(np.abs(t_stat), df))

    return r_partial, p_value


def calculate_confidence_interval(r: float, n: int, alpha: float = 0.05) -> Tuple[float, float]:
    """
    Calculates the confidence interval for a correlation coefficient using Fisher's z-transformation.

    Args:
        r: Correlation coefficient.
        n: Sample size.
        alpha: Significance level (default 0.05).

    Returns:
        Tuple[float, float]: (lower_bound, upper_bound)
    """
    if abs(r) >= 1.0:
        return (r, r)

    # Fisher's z-transformation
    z = 0.5 * np.log((1 + r) / (1 - r))
    se_z = 1.0 / np.sqrt(n - 3)

    z_crit = stats.norm.ppf(1 - alpha / 2)
    z_lower = z - z_crit * se_z
    z_upper = z + z_crit * se_z

    # Inverse transformation
    r_lower = (np.exp(2 * z_lower) - 1) / (np.exp(2 * z_lower) + 1)
    r_upper = (np.exp(2 * z_upper) - 1) / (np.exp(2 * z_upper) + 1)

    return r_lower, r_upper


def run_partial_correlation_analysis() -> Dict[str, Any]:
    """
    Runs the full partial correlation analysis on the loaded simulation data.

    Analyzes:
    1. Diffusion Rate vs Clustering Coefficient (controlling for Average Path Length)
    2. Diffusion Rate vs Average Path Length (controlling for Clustering Coefficient)

    Returns:
        Dict[str, Any]: A dictionary containing the results for each metric pair.
    """
    logger.info("Loading simulation data for partial correlation analysis...")
    df = load_simulation_data()

    results = {
        "metadata": {
            "total_samples": len(df),
            "analysis_type": "partial_correlation",
            "control_variable_description": "Average Path Length"
        },
        "pairs": []
    }

    # Define the pairs to analyze
    # Pair 1: X=Clustering, Y=Diffusion, Z=PathLength
    # Pair 2: X=PathLength, Y=Diffusion, Z=Clustering
    pairs_to_analyze = [
        {
            "x": "clustering_coefficient",
            "y": "diffusion_rate",
            "z": "average_path_length",
            "description": "Effect of Clustering on Diffusion (controlling for Path Length)"
        },
        {
            "x": "average_path_length",
            "y": "diffusion_rate",
            "z": "clustering_coefficient",
            "description": "Effect of Path Length on Diffusion (controlling for Clustering)"
        }
    ]

    for pair in pairs_to_analyze:
        x_col = pair['x']
        y_col = pair['y']
        z_col = pair['z']

        logger.info(f"Analyzing {pair['description']}...")

        x_vals = df[x_col].values
        y_vals = df[y_col].values
        z_vals = df[z_col].values

        try:
            r, p_val = calculate_partial_correlation(x_vals, y_vals, z_vals)
            ci_lower, ci_upper = calculate_confidence_interval(r, len(df))

            pair_result = {
                "x_variable": x_col,
                "y_variable": y_col,
                "control_variable": z_col,
                "description": pair['description'],
                "partial_correlation_coefficient": float(r) if not np.isnan(r) else None,
                "p_value": float(p_val) if not np.isnan(p_val) else None,
                "confidence_interval_95": [
                    float(ci_lower) if not np.isnan(ci_lower) else None,
                    float(ci_upper) if not np.isnan(ci_upper) else None
                ],
                "sample_size": len(df)
            }
            results["pairs"].append(pair_result)
            logger.info(f"  Result: r={r:.4f}, p={p_val:.4f}")

        except Exception as e:
            logger.error(f"Error analyzing pair {pair['description']}: {e}")
            results["pairs"].append({
                "x_variable": x_col,
                "y_variable": y_col,
                "control_variable": z_col,
                "description": pair['description'],
                "error": str(e)
            })

    return results


def save_results(results: Dict[str, Any], output_path: Optional[str] = None) -> Path:
    """
    Saves the analysis results to a JSON file.

    Args:
        results: The results dictionary.
        output_path: Optional path for the output file. Defaults to data/analysis/partial_correlation_results.json.

    Returns:
        Path: The path to the saved file.
    """
    if output_path is None:
        output_path = "data/analysis/partial_correlation_results.json"

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    with open(out_file, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Results saved to {out_file}")
    return out_file


def main() -> int:
    """
    Main entry point for the partial correlation analysis script.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        results = run_partial_correlation_analysis()
        save_results(results)
        logger.info("Partial correlation analysis completed successfully.")
        return 0
    except PartialCorrelationError as e:
        logger.error(f"Partial Correlation Error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
