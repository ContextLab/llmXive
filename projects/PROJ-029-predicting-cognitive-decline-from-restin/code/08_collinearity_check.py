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
from utils.io import load_csv, save_csv, ensure_dir
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


def main():
    """Main entry point for T044."""
    logger.info("Starting T044: Collinearity Check")

    # Load configuration (with graceful fallback)
    cfg = _load_config()
    data_dir: Path = cfg["data_dir"]

    input_path = data_dir / "graph_metrics.csv"
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error(
            "This script requires 'data/processed/graph_metrics.csv' to be "
            "generated first by code/03_compute_graph_metrics.py."
        )
        sys.exit(1)

    # Load the metrics CSV
    try:
        df = load_csv(input_path)
        logger.info(f"Loaded {len(df)} records from {input_path}")
    except Exception as exc:
        logger.error(f"Failed to load CSV: {exc}")
        sys.exit(1)

    # Verify required identifier column
    if "subject_id" not in df.columns:
        logger.error("Missing required column 'subject_id' in the input CSV.")
        sys.exit(1)

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
        result = {
            "status": "skipped",
            "reason": "insufficient numeric features",
            "input_file": str(input_path),
            "found_columns": list(df.columns),
        }
        output_path = data_dir / "collinearity_report.json"
        ensure_dir(output_path.parent)
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        print(json.dumps(result))
        return 0

    # Compute the correlation matrix for the numeric features
    try:
        corr_matrix = calculate_correlation_matrix(df[feature_cols])
    except Exception as exc:
        logger.error(f"Failed to calculate correlation matrix: {exc}")
        sys.exit(1)

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

    result = {
        "status": "success",
        "input_file": str(input_path),
        "total_features": len(feature_cols),
        "threshold": threshold,
        "highly_correlated_pairs": high_corr_pairs,
        "correlation_matrix_shape": list(corr_matrix.shape),
    }

    # Write the report
    output_path = data_dir / "collinearity_report.json"
    ensure_dir(output_path.parent)
    try:
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        logger.info(f"Wrote collinearity report to {output_path}")
    except Exception as exc:
        logger.error(f"Failed to write collinearity report: {exc}")
        sys.exit(1)

    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())