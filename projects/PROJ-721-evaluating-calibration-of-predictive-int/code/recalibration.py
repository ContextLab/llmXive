"""
Recalibration module implementing Adaptive Conformal Prediction (ACP).

This module provides post-processing functionality to adjust prediction intervals
based on observed calibration errors, ensuring empirical coverage matches nominal
levels as defined in the project configuration.
"""

from __future__ import annotations

import json
import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yaml

from metrics import empirical_coverage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_config(config_path: str = "config.yaml") -> Dict:
    """
    Load configuration parameters from the YAML file.

    Args:
        config_path: Path to the configuration file.

    Returns:
        Dictionary containing configuration parameters.

    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        logger.info(f"Loaded configuration from {config_path}")
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file: {e}")
        raise


def compute_nonconformity_scores(
    y_true: np.ndarray,
    y_pred_lower: np.ndarray,
    y_pred_upper: np.ndarray,
) -> np.ndarray:
    """
    Compute nonconformity scores for Adaptive Conformal Prediction.

    The nonconformity score measures how "strange" a point is relative to the
    prediction interval. Points outside the interval have higher scores.

    Args:
        y_true: Array of true values (ground truth).
        y_pred_lower: Array of lower bound predictions.
        y_pred_upper: Array of upper bound predictions.

    Returns:
        Array of nonconformity scores.
    """
    scores = np.zeros_like(y_true, dtype=float)

    # Points below lower bound
    below = y_true < y_pred_lower
    scores[below] = y_pred_lower[below] - y_true[below]

    # Points above upper bound
    above = y_true > y_pred_upper
    scores[above] = y_true[above] - y_pred_upper[above]

    # Points inside interval have score 0
    # (already initialized to 0)

    return scores


def compute_adaptive_weight(
    scores: np.ndarray,
    nominal_coverage: float,
    alpha: float = 0.05,
) -> float:
    """
    Compute the adaptive weight for recalibration.

    This function calculates the weight adjustment based on the observed
    nonconformity scores and the target nominal coverage level.

    Args:
        scores: Array of nonconformity scores.
        nominal_coverage: Target coverage level (e.g., 0.95).
        alpha: Smoothing parameter for stability (default 0.05).

    Returns:
        Adaptive weight factor to adjust interval bounds.
    """
    if len(scores) == 0:
        logger.warning("Empty scores array, returning default weight of 1.0")
        return 1.0

    # Sort scores to find quantile
    sorted_scores = np.sort(scores)
    n = len(sorted_scores)

    # Target quantile index
    target_idx = int(np.ceil(n * nominal_coverage)) - 1
    target_idx = min(target_idx, n - 1)  # Ensure within bounds

    # Get the quantile score
    quantile_score = sorted_scores[target_idx]

    # Compute weight adjustment based on deviation from nominal
    # If quantile_score > 0, we need to widen intervals
    # If quantile_score < 0 (shouldn't happen with our scoring), we narrow
    weight_adjustment = 1.0 + alpha * (quantile_score / (np.max(scores) + 1e-10))

    # Clamp weight to reasonable range [0.5, 2.0]
    weight = np.clip(weight_adjustment, 0.5, 2.0)

    logger.info(
        f"Computed adaptive weight: {weight:.4f} (quantile_score: {quantile_score:.4f})"
    )

    return weight


def apply_recalibration(
    y_pred_lower: np.ndarray,
    y_pred_upper: np.ndarray,
    weight: float,
    y_true: Optional[np.ndarray] = None,
    nominal_coverage: Optional[float] = None,
) -> Tuple[np.ndarray, np.ndarray, Dict]:
    """
    Apply recalibration to prediction intervals using adaptive weights.

    This function expands or contracts the prediction intervals based on the
    computed adaptive weight to improve coverage.

    Args:
        y_pred_lower: Array of lower bound predictions.
        y_pred_upper: Array of upper bound predictions.
        weight: Adaptive weight factor from compute_adaptive_weight.
        y_true: Optional array of true values for validation.
        nominal_coverage: Optional target coverage level for logging.

    Returns:
        Tuple containing:
            - recalibrated_lower: Adjusted lower bounds
            - recalibrated_upper: Adjusted upper bounds
            - metadata: Dictionary with recalibration details
    """
    # Calculate interval width
    interval_width = y_pred_upper - y_pred_lower

    # Apply weight adjustment (center the adjustment)
    adjustment = (interval_width * (weight - 1.0)) / 2.0

    recalibrated_lower = y_pred_lower - adjustment
    recalibrated_upper = y_pred_upper + adjustment

    # Prepare metadata
    metadata = {
        "original_width_mean": float(np.mean(interval_width)),
        "recalibrated_width_mean": float(np.mean(recalibrated_upper - recalibrated_lower)),
        "weight_applied": float(weight),
    }

    if y_true is not None and nominal_coverage is not None:
        original_cov = empirical_coverage(y_true, y_pred_lower, y_pred_upper)
        recalibrated_cov = empirical_coverage(y_true, recalibrated_lower, recalibrated_upper)
        metadata["original_coverage"] = float(original_cov)
        metadata["recalibrated_coverage"] = float(recalibrated_cov)
        metadata["coverage_improvement"] = float(recalibrated_cov - original_cov)

        logger.info(
            f"Coverage change: {original_cov:.4f} -> {recalibrated_cov:.4f} "
            f"(improvement: {recalibrated_cov - original_cov:.4f})"
        )

    return recalibrated_lower, recalibrated_upper, metadata


def run_acp_calibration(
    y_true: np.ndarray,
    y_pred_lower: np.ndarray,
    y_pred_upper: np.ndarray,
    nominal_coverage: float,
    config: Optional[Dict] = None,
) -> Tuple[np.ndarray, np.ndarray, Dict]:
    """
    Run the full Adaptive Conformal Prediction calibration pipeline.

    This is the main entry point for recalibration. It computes nonconformity
    scores, determines the adaptive weight, and applies recalibration.

    Args:
        y_true: Array of true values (ground truth).
        y_pred_lower: Array of lower bound predictions.
        y_pred_upper: Array of upper bound predictions.
        nominal_coverage: Target coverage level (e.g., 0.95).
        config: Optional configuration dictionary. If None, loads from config.yaml.

    Returns:
        Tuple containing:
            - recalibrated_lower: Adjusted lower bounds
            - recalibrated_upper: Adjusted upper bounds
            - metadata: Dictionary with calibration details
    """
    if config is None:
        config = load_config()

    # Extract alpha parameter from config if available
    alpha = config.get("aci_alpha", 0.05)

    logger.info(f"Starting ACP calibration for nominal coverage: {nominal_coverage}")

    # Step 1: Compute nonconformity scores
    scores = compute_nonconformity_scores(y_true, y_pred_lower, y_pred_upper)

    # Step 2: Compute adaptive weight
    weight = compute_adaptive_weight(scores, nominal_coverage, alpha)

    # Step 3: Apply recalibration
    recalibrated_lower, recalibrated_upper, metadata = apply_recalibration(
        y_pred_lower, y_pred_upper, weight, y_true, nominal_coverage
    )

    metadata["nominal_coverage"] = nominal_coverage
    metadata["alpha"] = alpha

    logger.info("ACP calibration completed successfully")

    return recalibrated_lower, recalibrated_upper, metadata


def save_recalibration_params(
    params: Dict,
    output_path: str = "results/recalibration_params.json",
) -> None:
    """
    Save recalibration parameters to a JSON file.

    Args:
        params: Dictionary of parameters to save.
        output_path: Path to the output JSON file.
    """
    import os
    from pathlib import Path

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(params, f, indent=2)

    logger.info(f"Saved recalibration parameters to {output_path}")


def process_multiple_series(
    series_data: List[Dict],
    nominal_levels: List[float],
    config: Optional[Dict] = None,
) -> pd.DataFrame:
    """
    Process multiple time series and apply recalibration.

    Args:
        series_data: List of dictionaries, each containing:
            - 'series_id': Identifier for the series
            - 'y_true': True values array
            - 'y_pred_lower': Lower predictions array
            - 'y_pred_upper': Upper predictions array
        nominal_levels: List of nominal coverage levels to process.
        config: Optional configuration dictionary.

    Returns:
        DataFrame with recalibration results for all series and levels.
    """
    results = []

    for series in series_data:
        series_id = series["series_id"]
        y_true = series["y_true"]
        y_pred_lower = series["y_pred_lower"]
        y_pred_upper = series["y_pred_upper"]

        for nominal in nominal_levels:
            try:
                rec_lower, rec_upper, metadata = run_acp_calibration(
                    y_true, y_pred_lower, y_pred_upper, nominal, config
                )

                results.append(
                    {
                        "series_id": series_id,
                        "nominal_coverage": nominal,
                        "original_coverage": metadata.get("original_coverage", np.nan),
                        "recalibrated_coverage": metadata.get("recalibrated_coverage", np.nan),
                        "improvement": metadata.get("coverage_improvement", np.nan),
                        "weight_applied": metadata.get("weight_applied", np.nan),
                    }
                )
            except Exception as e:
                logger.error(f"Error processing series {series_id} at level {nominal}: {e}")
                results.append(
                    {
                        "series_id": series_id,
                        "nominal_coverage": nominal,
                        "original_coverage": np.nan,
                        "recalibrated_coverage": np.nan,
                        "improvement": np.nan,
                        "weight_applied": np.nan,
                        "error": str(e),
                    }
                )

    return pd.DataFrame(results)


def main():
    """
    Main function to demonstrate recalibration functionality.
    Reads from config.yaml and processes sample data if available.
    """
    logger.info("Running recalibration module main function")

    # Load configuration
    try:
        config = load_config()
        nominal_levels = config.get("nominal_levels", [0.80, 0.95])
        logger.info(f"Using nominal levels: {nominal_levels}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return

    # Note: Actual data processing would be handled by run_pipeline.py
    # This main function serves as a module entry point for testing
    logger.info("Recalibration module ready for integration")


if __name__ == "__main__":
    main()
