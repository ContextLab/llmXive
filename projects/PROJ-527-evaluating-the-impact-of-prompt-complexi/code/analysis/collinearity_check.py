"""
Collinearity Check Module (T020a)

Implements the correlation check between token count and structural element count
to diagnose potential collinearity (FR-013).
Writes the correlation coefficient to data/results/analysis_summary.csv.
"""
import os
import csv
from pathlib import Path
from typing import Optional, Dict, Any, List
import pandas as pd
from scipy import stats

from config import Paths
from utils.logger import get_logger

logger = get_logger(__name__)

def calculate_collinearity(
    variants_path: Optional[Path] = None
) -> Dict[str, float]:
    """
    Calculate Pearson correlation between token_count and structural_element_count.

    Args:
        variants_path: Path to the parquet file containing prompt variants.
                       Defaults to Paths.PROCESSED / 'prompt_variants.parquet'.

    Returns:
        Dictionary containing:
            - 'pearson_r': Pearson correlation coefficient
            - 'p_value': P-value for the hypothesis test
            - 'n_samples': Number of samples used
    """
    if variants_path is None:
        variants_path = Paths.PROCESSED / "prompt_variants.parquet"

    if not variants_path.exists():
        raise FileNotFoundError(
            f"Prompt variants file not found at {variants_path}. "
            "Ensure T018 (storage) has been executed successfully."
        )

    logger.info(f"Loading prompt variants from {variants_path}")
    df = pd.read_parquet(variants_path)

    # Ensure required columns exist
    required_cols = ["token_count", "structural_element_count"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required columns in {variants_path}: {missing}"
        )

    # Drop rows with NaN in relevant columns
    clean_df = df.dropna(subset=required_cols)
    n_samples = len(clean_df)

    if n_samples < 2:
        logger.warning(
            f"Insufficient samples ({n_samples}) to calculate correlation."
        )
        return {
            "pearson_r": 0.0,
            "p_value": 1.0,
            "n_samples": n_samples
        }

    x = clean_df["token_count"]
    y = clean_df["structural_element_count"]

    # Calculate Pearson correlation
    r, p_value = stats.pearsonr(x, y)

    logger.info(
        f"Collinearity Check Results: "
        f"r={r:.4f}, p={p_value:.4e}, n={n_samples}"
    )

    return {
        "pearson_r": float(r),
        "p_value": float(p_value),
        "n_samples": int(n_samples)
    }

def write_summary_to_csv(
    results: Dict[str, float],
    output_path: Optional[Path] = None
) -> Path:
    """
    Write the correlation results to data/results/analysis_summary.csv.

    If the file exists, it appends a new row. If not, it creates the file
    with headers.

    Args:
        results: Dictionary containing correlation metrics.
        output_path: Path to the output CSV. Defaults to Paths.RESULTS / 'analysis_summary.csv'.

    Returns:
        Path to the written file.
    """
    if output_path is None:
        output_path = Paths.RESULTS / "analysis_summary.csv"

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Prepare row data
    row = {
        "test_type": "collinearity_check",
        "test_statistic": results["pearson_r"],
        "p_value": results["p_value"],
        "effect_size": results["pearson_r"], # Using r as effect size for correlation
        "corrected_p_value": results["p_value"], # No correction needed for single test
        "covariate_adjusted_p_value": None,
        "correlation_coefficient": results["pearson_r"],
        "n_samples": results["n_samples"]
    }

    # Check if file exists to determine if headers are needed
    file_exists = output_path.exists()
    headers = list(row.keys())

    with open(output_path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    logger.info(f"Wrote collinearity check results to {output_path}")
    return output_path

def main() -> None:
    """
    Main entry point for the collinearity check task (T020a).
    Loads data, calculates correlation, and writes results to CSV.
    """
    try:
        results = calculate_collinearity()
        output_file = write_summary_to_csv(results)
        logger.info(f"Task T020a completed successfully. Output: {output_file}")
    except Exception as e:
        logger.error(f"Task T020a failed: {e}")
        raise

if __name__ == "__main__":
    main()
