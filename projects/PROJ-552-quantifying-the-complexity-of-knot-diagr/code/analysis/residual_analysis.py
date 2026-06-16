"""
Residual Analysis Module
========================

This script performs residual analysis on the cleaned knot dataset to
identify hyperbolic knot families whose hyperbolic volume deviates
significantly (≥ 2 standard deviations) from a simple linear model
relating crossing number to hyperbolic volume.

The script is invoked as a stand‑alone entry point::

    python code/analysis/residual_analysis.py

It produces two artefacts:

1. ``docs/reproducibility/residual_analysis.md`` – a markdown report
   summarising the residual statistics and listing outlier knots.
2. ``data/processed/outlier_knots.json`` – a JSON file containing the
   identifiers of knots that are statistical outliers.

The implementation follows the project's reproducibility conventions
(see ``code/reproducibility/logs.py``) by logging the operation with
``log_operation``.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

# Project‑specific logging utilities
from reproducibility.logs import get_logger, log_operation

__all__ = [
    "ResidualEntry",
    "ResidualAnalysisResult",
    "ResidualAnalysisReport",
    "load_cleaned_knots",
    "fit_linear_model",
    "calculate_residuals",
    "standardize_residuals",
    "group_by_crossing_number",
    "group_by_classification",
    "identify_outliers",
    "generate_residual_analysis_report",
    "save_outlier_knots_json",
    "main",
]


@dataclass
class ResidualEntry:
    """Single residual record for a knot."""

    knot_id: str
    crossing_number: int
    braid_index: int
    hyperbolic_volume: float
    predicted_volume: float
    residual: float
    z_score: float
    classification: str  # e.g. "alternating" or "non-alternating"


@dataclass
class ResidualAnalysisResult:
    """Container for the full residual analysis."""

    residuals: List[ResidualEntry]
    outliers: List[ResidualEntry]
    summary_by_crossing: Dict[int, Dict[str, float]]
    summary_by_classification: Dict[str, Dict[str, float]]


@dataclass
class ResidualAnalysisReport:
    """Markdown report representation."""

    title: str
    summary: str
    outlier_section: str

    def render(self) -> str:
        """Render the report as a markdown string."""
        parts = [f"# {self.title}", "", self.summary, "", self.outlier_section]
        return "\n".join(parts)


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def load_cleaned_knots(data_path: Path | str = Path("data/processed/knots_cleaned.csv")) -> pd.DataFrame:
    """
    Load the cleaned knot dataset.

    Parameters
    ----------
    data_path: Path | str
        Path to the CSV file produced by the cleaning pipeline.

    Returns
    -------
    pd.DataFrame
        DataFrame with at least the following columns:
        ``knot_id``, ``crossing_number``, ``braid_index``,
        ``hyperbolic_volume``, ``alternating``.
    """
    data_path = Path(data_path)
    if not data_path.is_file():
        raise FileNotFoundError(f"Cleaned data file not found: {data_path}")

    df = pd.read_csv(data_path, dtype={"knot_id": str})
    required = {"knot_id", "crossing_number", "braid_index", "hyperbolic_volume", "alternating"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in cleaned data: {missing}")

    return df


def fit_linear_model(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """
    Fit a simple linear regression (ordinary least squares) to predict ``y`` from ``x``.

    Returns
    -------
    slope, intercept
    """
    if len(x) == 0:
        raise ValueError("Empty input arrays for linear model fitting.")
    # Using numpy's polyfit for a degree‑1 polynomial
    slope, intercept = np.polyfit(x, y, 1)
    return float(slope), float(intercept)


def calculate_residuals(df: pd.DataFrame) -> List[ResidualEntry]:
    """
    Compute residuals of hyperbolic volume relative to a linear model
    using crossing number as the predictor.

    Returns a list of ``ResidualEntry`` objects.
    """
    # Prepare predictor and response arrays
    x = df["crossing_number"].to_numpy(dtype=float)
    y = df["hyperbolic_volume"].to_numpy(dtype=float)

    slope, intercept = fit_linear_model(x, y)

    residuals = []
    for _, row in df.iterrows():
        predicted = slope * row["crossing_number"] + intercept
        resid = row["hyperbolic_volume"] - predicted
        # Placeholder for z‑score; will be filled after standardisation
        residuals.append(
            ResidualEntry(
                knot_id=row["knot_id"],
                crossing_number=int(row["crossing_number"]),
                braid_index=int(row["braid_index"]),
                hyperbolic_volume=float(row["hyperbolic_volume"]),
                predicted_volume=predicted,
                residual=resid,
                z_score=0.0,  # to be updated
                classification=str(row["alternating"]).lower(),
            )
        )
    return residuals


def standardize_residuals(residuals: List[ResidualEntry]) -> None:
    """
    Compute z‑scores for residuals in‑place.
    """
    values = np.array([r.residual for r in residuals], dtype=float)
    mean = values.mean()
    std = values.std(ddof=0) or 1.0  # avoid division by zero
    for r in residuals:
        r.z_score = (r.residual - mean) / std


def group_by_crossing_number(residuals: List[ResidualEntry]) -> Dict[int, List[float]]:
    """
    Group residuals by crossing number.
    """
    groups: Dict[int, List[float]] = defaultdict(list)
    for r in residuals:
        groups[r.crossing_number].append(r.residual)
    return groups


def group_by_classification(residuals: List[ResidualEntry]) -> Dict[str, List[float]]:
    """
    Group residuals by alternating / non‑alternating classification.
    """
    groups: Dict[str, List[float]] = defaultdict(list)
    for r in residuals:
        groups[r.classification].append(r.residual)
    return groups


def _summary_statistics(values: List[float]) -> Dict[str, float]:
    """
    Compute mean and standard deviation for a list of numbers.
    """
    arr = np.array(values, dtype=float)
    return {
        "mean": float(arr.mean()) if arr.size else float("nan"),
        "std": float(arr.std(ddof=0)) if arr.size else float("nan"),
    }


def identify_outliers(residuals: List[ResidualEntry], threshold: float = 2.0) -> List[ResidualEntry]:
    """
    Return residual entries whose absolute z‑score exceeds ``threshold``.
    """
    return [r for r in residuals if abs(r.z_score) >= threshold]


def generate_residual_analysis_report(
    result: ResidualAnalysisResult,
) -> ResidualAnalysisReport:
    """
    Build a markdown report from the analysis result.
    """
    # Summary statistics
    crossing_stats = {
        cn: _summary_statistics(vals) for cn, vals in group_by_crossing_number(result.residuals).items()
    }
    class_stats = {
        cl: _summary_statistics(vals) for cl, vals in group_by_classification(result.residuals).items()
    }

    # Render summary tables
    def _render_table(stats: Dict) -> str:
        lines = ["| Group | Mean Residual | Std Dev |", "|---|---|---|"]
        for key, s in sorted(stats.items()):
            lines.append(f"| {key} | {s['mean']:.3f} | {s['std']:.3f} |")
        return "\n".join(lines)

    summary_md = (
        "## Summary Statistics\n\n"
        "### By Crossing Number\n\n"
        + _render_table(crossing_stats)
        + "\n\n### By Classification (alternating / non‑alternating)\n\n"
        + _render_table(class_stats)
    )

    # Outlier section
    if result.outliers:
        outlier_lines = ["| Knot ID | Crossing | Braid Index | Volume | Predicted | Residual | Z‑Score | Classification |"]
        outlier_lines.append("|---|---|---|---|---|---|---|---|")
        for o in result.outliers:
            outlier_lines.append(
                f"| {o.knot_id} | {o.crossing_number} | {o.braid_index} | {o.hyperbolic_volume:.3f} | "
                f"{o.predicted_volume:.3f} | {o.residual:.3f} | {o.z_score:.2f} | {o.classification} |"
            )
        outlier_md = "## Outlier Knots (|Z| ≥ 2)\n\n" + "\n".join(outlier_lines)
    else:
        outlier_md = "## Outlier Knots\n\nNo knots exceeded the ±2 σ threshold."

    return ResidualAnalysisReport(
        title="Residual Analysis of Hyperbolic Volume",
        summary=summary_md,
        outlier_section=outlier_md,
    )


def save_outlier_knots_json(outliers: List[ResidualEntry], output_path: Path) -> None:
    """
    Persist outlier knot identifiers (and a few key fields) to JSON.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = [asdict(o) for o in outliers]
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the residual analysis pipeline.

    The function:
    1. Loads the cleaned dataset.
    2. Computes residuals against a linear crossing‑number model.
    3. Standardises residuals (z‑scores).
    4. Identifies outliers (|z| ≥ 2).
    5. Writes a markdown report and a JSON file of outliers.
    6. Logs the operation using the project's reproducibility logger.
    """
    logger = get_logger()
    data_file = Path("data/processed/knots_cleaned.csv")
    report_file = Path("docs/reproducibility/residual_analysis.md")
    outlier_json = Path("data/processed/outlier_knots.json")

    # ------------------------------------------------------------------
    # Step 1 – load data
    # ------------------------------------------------------------------
    df = load_cleaned_knots(data_file)

    # ------------------------------------------------------------------
    # Step 2 – compute residuals
    # ------------------------------------------------------------------
    residual_entries = calculate_residuals(df)

    # ------------------------------------------------------------------
    # Step 3 – standardise residuals
    # ------------------------------------------------------------------
    standardize_residuals(residual_entries)

    # ------------------------------------------------------------------
    # Step 4 – identify outliers
    # ------------------------------------------------------------------
    outliers = identify_outliers(residual_entries, threshold=2.0)

    # ------------------------------------------------------------------
    # Step 5 – generate and write the report
    # ------------------------------------------------------------------
    result = ResidualAnalysisResult(
        residuals=residual_entries,
        outliers=outliers,
        summary_by_crossing=group_by_crossing_number(residual_entries),
        summary_by_classification=group_by_classification(residual_entries),
    )
    report = generate_residual_analysis_report(result)

    report_file.parent.mkdir(parents=True, exist_ok=True)
    with report_file.open("w", encoding="utf-8") as f:
        f.write(report.render())

    # ------------------------------------------------------------------
    # Step 6 – write outlier JSON
    # ------------------------------------------------------------------
    save_outlier_knots_json(outliers, outlier_json)

    # ------------------------------------------------------------------
    # Step 7 – log operation
    # ------------------------------------------------------------------
    try:
        # ``log_operation`` expects operation name and the primary input / output files.
        # Additional keyword arguments are ignored if the implementation does not support them.
        log_operation(
            operation="residual_analysis",
            input_file=str(data_file),
            output_file=str(report_file),
        )
    except TypeError:
        # Fallback: call without extra arguments if the signature is stricter.
        logger.info("Residual analysis completed (log_operation signature mismatch).")

    logger.info("Residual analysis finished successfully.")


if __name__ == "__main__":
    main()