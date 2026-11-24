"""
Wrapper script that runs the sensitivity analysis defined in ``code.analysis``.
The resulting JSON is written to ``data/processed/sensitivity_analysis.json``.
"""

import logging
from pathlib import Path

import pandas as pd

from llmxive_toolkit import paths, get_logger

from code.analysis import run_sensitivity_analysis

log = get_logger(__name__)

def main() -> int:
    descriptors_path = paths.data("processed", "descriptors.csv")
    if not descriptors_path.exists():
        log.error(f"Descriptors file missing: {descriptors_path}")
        return 1

    df = pd.read_csv(descriptors_path)

    # Expected columns: target and feature columns
    target_col = None
    for cand in ["log_conductivity", "log_conductivity_proxy", "conductivity"]:
        if cand in df.columns:
            target_col = cand
            break
    if target_col is None:
        log.error("No suitable target column found for sensitivity analysis.")
        return 1

    feature_cols = [c for c in df.columns if c not in [target_col, "smiles"]]

    thresholds = [2.5, 3.0, 3.5]  # matches config SENSITIVITY_THRESHOLDS

    results = run_sensitivity_analysis(df, target_col, thresholds, feature_cols)

    out_path = paths.data("processed", "sensitivity_analysis.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        import json

        json.dump(results, f, indent=2)
    log.info(f"Sensitivity analysis written to {out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
