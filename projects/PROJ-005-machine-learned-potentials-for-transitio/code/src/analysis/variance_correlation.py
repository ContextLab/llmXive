"""
Compute ensemble variance and correlation with error magnitude.

This module implements Task T026:
- Input: code/data/processed/residuals.parquet (from T025)
- Output: code/data/results/variance_correlation.json
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd

from src.utils.logging import setup_logger, get_logger

logger = get_logger(__name__)

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parents[3]

def load_residuals(residuals_path: Path) -> pd.DataFrame:
    """
    Load the residuals parquet file.

    Expected columns based on T025 schema:
    - sample_id (str)
    - error_ml_dft (float): ML prediction - DFT reference
    - ligand_class (str)
    - metal_center (str)
    - ensemble_variance (float): Variance of the ensemble predictions for this sample.
      (Added by T023c/T025 logic; if missing, we compute it from raw predictions if available,
       but the schema implies it should be present. If truly missing, we fail loudly.)
    """
    if not residuals_path.exists():
        raise FileNotFoundError(f"Residuals file not found: {residuals_path}")

    df = pd.read_parquet(residuals_path)

    required_cols = ["sample_id", "error_ml_dft", "ensemble_variance"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Residuals file missing required columns: {missing_cols}")

    # Ensure numeric types
    df["error_ml_dft"] = pd.to_numeric(df["error_ml_dft"], errors="raise")
    df["ensemble_variance"] = pd.to_numeric(df["ensemble_variance"], errors="raise")

    # Drop rows with NaN in critical columns
    df = df.dropna(subset=required_cols)

    if df.empty:
        raise ValueError("Residuals file is empty after dropping NaNs.")

    return df

def compute_correlation_metrics(df: pd.DataFrame) -> Tuple[float, float]:
    """
    Compute Pearson correlation between error magnitude and ensemble variance.

    Returns:
        pearson_correlation: Pearson r between |error_ml_dft| and ensemble_variance
        mean_variance: Mean of ensemble_variance
    """
    errors = df["error_ml_dft"].values
    variances = df["ensemble_variance"].values

    # Use absolute error magnitude as per SC-005 (correlation with error magnitude)
    error_magnitude = np.abs(errors)

    # Filter out zero variance cases if they cause issues (though Pearson handles it)
    # But if all variances are zero, correlation is undefined.
    if np.all(variances == 0):
        logger.warning("All ensemble variances are zero; correlation is undefined. Setting to 0.0.")
        return 0.0, 0.0

    # Compute Pearson correlation
    # np.corrcoef returns a 2x2 matrix; [0,1] is the correlation between x and y
    corr_matrix = np.corrcoef(error_magnitude, variances)
    pearson_r = corr_matrix[0, 1]

    # Handle NaN if one variable is constant
    if np.isnan(pearson_r):
        logger.warning("Pearson correlation is NaN (likely constant variance). Setting to 0.0.")
        pearson_r = 0.0

    mean_var = float(np.mean(variances))

    return float(pearson_r), mean_var

def save_results(
    pearson_correlation: float,
    mean_variance: float,
    output_path: Path
) -> None:
    """Save the results to a JSON file."""
    result = {
        "pearson_correlation": pearson_correlation,
        "mean_variance": mean_variance
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    logger.info(f"Saved variance correlation results to {output_path}")

def run_variance_correlation_analysis(
    residuals_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Dict[str, float]:
    """
    Main entry point for Task T026.

    Args:
        residuals_path: Path to residuals.parquet. Defaults to project default.
        output_path: Path to output JSON. Defaults to project default.

    Returns:
        Dictionary with pearson_correlation and mean_variance.
    """
    project_root = get_project_root()

    if residuals_path is None:
        residuals_path = project_root / "code" / "data" / "processed" / "residuals.parquet"
    if output_path is None:
        output_path = project_root / "code" / "data" / "results" / "variance_correlation.json"

    logger.info(f"Loading residuals from {residuals_path}")
    df = load_residuals(residuals_path)
    logger.info(f"Loaded {len(df)} samples for analysis")

    logger.info("Computing correlation between error magnitude and ensemble variance")
    pearson_r, mean_var = compute_correlation_metrics(df)

    logger.info(f"Pearson Correlation (|error| vs variance): {pearson_r:.4f}")
    logger.info(f"Mean Variance: {mean_var:.6f}")

    save_results(pearson_r, mean_var, output_path)

    return {
        "pearson_correlation": pearson_r,
        "mean_variance": mean_var
    }

def main() -> None:
    """CLI entry point."""
    setup_logger(level=logging.INFO)
    try:
        run_variance_correlation_analysis()
        logger.info("T026 variance correlation analysis completed successfully.")
    except Exception as e:
        logger.error(f"T026 analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
