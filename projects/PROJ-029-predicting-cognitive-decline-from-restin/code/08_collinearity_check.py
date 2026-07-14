"""
T044: Collinearity Check Script
Reconciles run‑book invocation with implementation.
Performs collinearity analysis on graph metrics and outputs a report.
"""
import sys
import json
from pathlib import Path

import pandas as pd

from utils.logger import get_logger
from utils.stats import calculate_correlation_matrix, check_collinearity
from utils.io import load_csv, ensure_dir
from config import get_config

# Initialise a tolerant logger – it accepts any call signature.
logger = get_logger("collinearity_check")


def _load_config():
    """
    Load the project configuration safely.

    The original implementation assumed a ``data`` section with a
    ``processed`` key, but some configurations (or early‑stage runs) may
    omit this.  We fall back to the conventional ``data/processed`` path
    when the expected keys are missing.
    """
    try:
        cfg = get_config()
    except Exception as exc:  # pragma: no cover – defensive
        logger.warning(f"Failed to load config via get_config(): {exc}")
        cfg = {}

    # Resolve the processed data directory, defaulting to ``data/processed``.
    data_dir = Path(
        cfg.get("data", {})
           .get("processed", "data/processed")
    )
    return {"data_dir": data_dir}


def _write_report(report: dict, output_path: Path) -> None:
    """Utility to write JSON report, ensuring parent directory exists."""
    ensure_dir(output_path.parent)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Wrote collinearity report to {output_path}")


def main() -> int:
    """Main entry point for T044."""
    logger.info("Starting T044: Collinearity Check")

    # Load configuration (with graceful fallback)
    cfg = _load_config()
    data_dir: Path = cfg["data_dir"]

    input_path = data_dir / "graph_metrics.csv"
    output_path = data_dir / "collinearity_report.json"

    # If the required input does not exist, gracefully skip processing.
    if not input_path.exists():
        logger.warning(
            f"Input file not found: {input_path}. "
            "Skipping collinearity analysis but generating a placeholder report."
        )
        report = {
            "status": "skipped",
            "reason": "graph_metrics.csv not found",
            "input_file": str(input_path),
            "output_file": str(output_path),
        }
        _write_report(report, output_path)
        print(json.dumps(report))
        return 0

    # Load the metrics CSV
    try:
        df = load_csv(input_path)
        logger.info(f"Loaded {len(df)} records from {input_path}")
    except Exception as exc:
        logger.error(f"Failed to load CSV: {exc}")
        report = {
            "status": "error",
            "reason": f"failed to load CSV: {exc}",
            "input_file": str(input_path),
        }
        _write_report(report, output_path)
        print(json.dumps(report))
        return 1

    # Verify required identifier column
    if "subject_id" not in df.columns:
        logger.error("Missing required column 'subject_id' in the input CSV.")
        report = {
            "status": "error",
            "reason": "missing subject_id column",
            "input_file": str(input_path),
        }
        _write_report(report, output_path)
        print(json.dumps(report))
        return 1

    # Identify numeric feature columns (exclude subject_id)
    feature_cols = [
        col for col in df.columns
        if col != "subject_id" and pd.api.types.is_numeric_dtype(df[col])
    ]

    if len(feature_cols) < 2:
        logger.warning(
            "Not enough numeric features to perform collinearity analysis "
            f"(found {len(feature_cols)})."
        )
        report = {
            "status": "skipped",
            "reason": "insufficient numeric features",
            "input_file": str(input_path),
            "found_columns": list(df.columns),
        }
        _write_report(report, output_path)
        print(json.dumps(report))
        return 0

    # Compute the correlation matrix for the numeric features
    try:
        corr_matrix = calculate_correlation_matrix(df[feature_cols])
    except Exception as exc:
        logger.error(f"Failed to calculate correlation matrix: {exc}")
        report = {
            "status": "error",
            "reason": f"correlation calculation failed: {exc}",
            "input_file": str(input_path),
        }
        _write_report(report, output_path)
        print(json.dumps(report))
        return 1

    # Detect highly correlated feature pairs
    threshold = 0.95
    high_corr_pairs = []
    for i in range(len(feature_cols)):
        for j in range(i + 1, len(feature_cols)):
            corr_val = corr_matrix.iloc[i, j]
            if abs(corr_val) > threshold:
                high_corr_pairs.append({
                    "feature1": feature_cols[i],
                    "feature2": feature_cols[j],
                    "correlation": float(corr_val),
                })

    report = {
        "status": "success",
        "input_file": str(input_path),
        "total_features": len(feature_cols),
        "threshold": threshold,
        "highly_correlated_pairs": high_corr_pairs,
        "correlation_matrix_shape": list(corr_matrix.shape),
    }

    _write_report(report, output_path)
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
