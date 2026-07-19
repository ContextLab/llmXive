"""
Residual Analysis Module for Knot Complexity Analysis.

This module contains logic for identifying families deviating >= 2 SD from
regression model predictions, as required by SC-011.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from code.reproducibility.logs import get_logger, log_operation

logger = get_logger(__name__)


@dataclass
class LinearModelResult:
    """Result of a linear model fit (re-exported for compatibility)."""
    model_type: str
    formula: str
    metrics: Any  # RegressionMetrics
    fitted_values: List[float]
    residuals: List[float]
    summary_text: str


@dataclass
class ResidualEntry:
    """Entry for residual analysis."""
    knot_id: str
    family: str
    crossing_number: float
    braid_index: float
    hyperbolic_volume: float
    predicted_volume: float
    residual: float
    standardized_residual: float


@log_operation
def calculate_residuals(
    observed: np.ndarray,
    predicted: np.ndarray
) -> np.ndarray:
    """
    Calculate residuals between observed and predicted values.

    Args:
        observed: Array of observed values.
        predicted: Array of predicted values.

    Returns:
        Array of residuals.
    """
    if len(observed) != len(predicted):
        raise ValueError("Observed and predicted arrays must have the same length.")
    return observed - predicted


@log_operation
def identify_outliers(
    df: pd.DataFrame,
    residuals: List[float],
    family_col: str = "family",
    threshold_sd: float = 2.0
) -> List[ResidualEntry]:
    """
    Identify knot families with residuals deviating >= threshold_sd standard deviations.

    Args:
        df: DataFrame with knot data.
        residuals: List of residuals corresponding to the DataFrame rows.
        family_col: Column name for knot families.
        threshold_sd: Number of standard deviations for outlier detection.

    Returns:
        List of ResidualEntry objects for outliers.
    """
    if len(residuals) == 0:
        return []

    mean_res = np.mean(residuals)
    std_res = np.std(residuals)

    if std_res == 0:
        logger.log("residual_identify_outliers", parameters={"message": "Standard deviation is zero, no outliers"})
        return []

    outliers = []
    for idx, res in enumerate(residuals):
        std_res_val = (res - mean_res) / std_res
        if abs(std_res_val) >= threshold_sd:
            row = df.iloc[idx]
            entry = ResidualEntry(
                knot_id=str(row.get("knot_id", f"idx_{idx}")),
                family=str(row.get(family_col, "Unknown")),
                crossing_number=float(row.get("crossing_number", 0)),
                braid_index=float(row.get("braid_index", 0)),
                hyperbolic_volume=float(row.get("hyperbolic_volume", 0)),
                predicted_volume=float(row.get("predicted_volume", 0)),
                residual=float(res),
                standardized_residual=float(std_res_val)
            )
            outliers.append(entry)

    logger.log("residual_outliers_identified", parameters={"count": len(outliers), "threshold": threshold_sd})
    return outliers


@log_operation
def save_outlier_knots_json(
    outliers: List[ResidualEntry],
    output_path: Path
) -> None:
    """
    Save outlier knots to a JSON file.

    Args:
        outliers: List of ResidualEntry objects.
        output_path: Path to the output JSON file.
    """
    data = [asdict(o) for o in outliers]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    logger.log("outlier_knots_saved", parameters={"path": str(output_path), "count": len(outliers)})


@log_operation
def main() -> None:
    """
    Main entry point for residual analysis.
    Loads data, calculates residuals, and identifies outliers.
    """
    logger.log("residual_analysis_start", parameters={})

    # Load data
    data_path = Path("data/processed/knots_cleaned.csv")
    if not data_path.exists():
        logger.log("residual_analysis_error", parameters={"error": "Data file not found"})
        raise FileNotFoundError(f"Data file not found: {data_path}")

    df = pd.read_csv(data_path)

    # Simple example: Calculate residuals for a linear fit of Volume vs Crossing
    # In a real pipeline, residuals would come from model_fitting.py
    x = df["crossing_number"].values
    y = df["hyperbolic_volume"].values

    # Linear fit
    slope, intercept, _, _, _ = np.polyfit(x, y, 1, full=False)
    predicted = slope * x + intercept
    residuals = calculate_residuals(y, predicted)

    # Identify outliers
    outliers = identify_outliers(df, residuals.tolist(), threshold_sd=2.0)

    # Save results
    output_path = Path("data/reports/residual_outliers.json")
    save_outlier_knots_json(outliers, output_path)

    logger.log("residual_analysis_complete", parameters={"outliers_count": len(outliers)})


if __name__ == "__main__":
    main()
