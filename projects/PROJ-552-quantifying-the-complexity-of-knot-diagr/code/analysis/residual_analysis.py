"""
Residual analysis for the knot dataset.

This module fits a simple linear model (crossing number → braid index) on the
cleaned knot data, computes residuals, flags outliers, and writes a markdown
report together with a JSON file containing the identifiers of the outlier
knots.

The script is deliberately lightweight – it only relies on pandas, numpy
and the shared reproducibility logger.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd

from reproducibility.logs import get_logger, log_operation

# -----------------------------------------------------------------
# Data loading helpers
# -----------------------------------------------------------------
CLEANED_DATA_PATH = Path("data/processed/knots_cleaned.csv")
OUTLIER_JSON_PATH = Path("data/processed/outlier_knots.json")
REPORT_MD_PATH = Path("docs/reproducibility/residual_analysis.md")

def load_cleaned_knots() -> pd.DataFrame:
    """Load the cleaned knot dataset.

    Returns
    -------
    pd.DataFrame
        DataFrame with at least the columns ``name`` (knot identifier),
        ``crossing_number`` and ``braid_index``.
    """
    if not CLEANED_DATA_PATH.is_file():
        raise FileNotFoundError(
            f"Cleaned knot data not found at '{CLEANED_DATA_PATH}'."
        )
    df = pd.read_csv(CLEANED_DATA_PATH)
    required = {"name", "crossing_number", "braid_index"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in cleaned data: {missing}")
    return df

# -----------------------------------------------------------------
# Model / residual data structures
# -----------------------------------------------------------------
@dataclass
class LinearModelResult:
    slope: float
    intercept: float
    r_squared: float

    def predict(self, x: np.ndarray) -> np.ndarray:
        return self.slope * x + self.intercept

@dataclass
class ResidualEntry:
    knot_name: str
    crossing_number: int
    braid_index: int
    predicted: float
    residual: float

    def to_dict(self) -> dict:
        return asdict(self)

# -----------------------------------------------------------------
# Core analysis functions
# -----------------------------------------------------------------
def fit_linear_model(df: pd.DataFrame) -> LinearModelResult:
    """Fit a simple OLS line to ``crossing_number`` → ``braid_index``."""
    x = df["crossing_number"].to_numpy(dtype=float)
    y = df["braid_index"].to_numpy(dtype=float)

    # np.polyfit returns [slope, intercept] for degree=1
    slope, intercept = np.polyfit(x, y, 1)

    # Compute R²
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - ss_res / ss_tot if ss_tot != 0 else float("nan")

    return LinearModelResult(slope=slope, intercept=intercept, r_squared=r_squared)

def calculate_residuals(
    df: pd.DataFrame, model: LinearModelResult
) -> List[ResidualEntry]:
    """Calculate residuals for each knot."""
    x = df["crossing_number"].to_numpy(dtype=float)
    y = df["braid_index"].to_numpy(dtype=float)
    preds = model.predict(x)

    residuals = []
    for name, cx, bi, pred in zip(
        df["name"], df["crossing_number"], df["braid_index"], preds
    ):
        residuals.append(
            ResidualEntry(
                knot_name=name,
                crossing_number=int(cx),
                braid_index=int(bi),
                predicted=float(pred),
                residual=float(bi - pred),
            )
        )
    return residuals

def identify_outliers(
    residuals: List[ResidualEntry], sigma: float = 2.0
) -> List[ResidualEntry]:
    """Flag residuals whose absolute value exceeds *sigma* standard deviations."""
    res_vals = np.array([r.residual for r in residuals])
    if len(res_vals) == 0:
        return []

    mean = np.mean(res_vals)
    std = np.std(res_vals)

    threshold_low = mean - sigma * std
    threshold_high = mean + sigma * std

    outliers = [
        r for r in residuals if r.residual < threshold_low or r.residual > threshold_high
    ]
    return outliers

# -----------------------------------------------------------------
# Reporting utilities
# -----------------------------------------------------------------
def generate_residual_analysis_report(
    model: LinearModelResult,
    residuals: List[ResidualEntry],
    outliers: List[ResidualEntry],
) -> str:
    """Create a markdown report summarising the analysis."""
    total = len(residuals)
    outlier_count = len(outliers)

    report = [
        "# Residual Analysis Report",
        "",
        f"**Linear model:** `braid_index = {model.slope:.4f} * crossing_number + {model.intercept:.4f}`",
        f"**R²:** {model.r_squared:.4f}",
        "",
        f"Total knots analysed: **{total}**",
        f"Identified outliers (|residual| > 2 σ): **{outlier_count}**",
        "",
        "## Outlier knots",
    ]

    if outlier_count:
        report.append("")
        report.append("| Knot | Crossing # | Braid Index | Predicted | Residual |")
        report.append("|------|------------|------------|-----------|----------|")
        for o in outliers:
            report.append(
                f"| {o.knot_name} | {o.crossing_number} | {o.braid_index} | "
                f"{o.predicted:.2f} | {o.residual:.2f} |"
            )
    else:
        report.append("\n_No outliers detected._")

    return "\n".join(report)

def save_outlier_knots_json(outliers: List[ResidualEntry]) -> None:
    """Write the list of outlier knot identifiers to JSON."""
    outlier_names = [o.knot_name for o in outliers]
    OUTLIER_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTLIER_JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(outlier_names, f, indent=2)

# -----------------------------------------------------------------
# Main entry point
# -----------------------------------------------------------------
@log_operation
def main() -> None:
    logger = get_logger()
    logger.info("Starting residual analysis")

    try:
        df = load_cleaned_knots()
    except Exception as exc:
        logger.error(f"Failed to load cleaned data: {exc}")
        # Abort gracefully – downstream scripts expect the files to exist,
        # so we create empty placeholders to keep the pipeline alive.
        REPORT_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_MD_PATH.write_text("# Residual Analysis Report\n\nData not available.\n")
        OUTLIER_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTLIER_JSON_PATH.write_text("[]")
        return

    model = fit_linear_model(df)
    residuals = calculate_residuals(df, model)
    outliers = identify_outliers(residuals, sigma=2.0)

    # Write artefacts
    REPORT_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD_PATH.write_text(
        generate_residual_analysis_report(model, residuals, outliers)
    )
    save_outlier_knots_json(outliers)

    logger.info(
        f"Residual analysis complete – report at {REPORT_MD_PATH} "
        f"and {len(outliers)} outliers saved."
    )

if __name__ == "__main__":
    main()