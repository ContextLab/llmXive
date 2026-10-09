"""
analysis.tradeoff_model
-----------------------

This module provides utilities for performing VIF (Variance Inflation Factor)
analysis on the processed execution logs.  It is used by the pipeline and
unit‑tests.  The original implementation lacked the ``VIF_THRESHOLD`` constant,
which caused an ``ImportError`` in the test suite (see
``tests/unit/test_vif_analysis.py``).  The constant is defined here and the
public API is left unchanged.

The rest of the module is unchanged from the original repository – only the
missing constant is added.
"""

import json
import os
import sys
import warnings
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

# ----------------------------------------------------------------------
# Public constant – required by the test suite
# ----------------------------------------------------------------------
# The threshold at which the VIF metric is considered to indicate problematic
# multicollinearity.  A conventional value is 5.0; the tests reference this
# constant to verify that the analysis respects the bound.
VIF_THRESHOLD: float = 5.0

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def load_processed_logs(processed_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all processed execution logs from the directory.
    """
    logs = []
    for file_path in processed_dir.glob("*.json"):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                logs.extend(data)
            else:
                logs.append(data)
    return logs

def filter_invalid_workflows_from_logs(logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter out any workflow logs where ``is_valid`` == False.
    """
    return [log for log in logs if log.get("is_valid", True)]

def calculate_vif(features: List[np.ndarray]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor for a list of feature arrays.
    Returns a mapping from feature name to its VIF value.
    """
    if not features:
        return {}

    # Build a DataFrame – the caller must ensure column order matches names
    df = pd.DataFrame({f"X{i}": col for i, col in enumerate(features, start=1)})

    vif_dict = {}
    for i in range(df.shape[1]):
        vif = variance_inflation_factor(df.values, i)
        vif_dict[f"X{i+1}"] = float(vif)
    return vif_dict

def run_vif_analysis(logs: Optional[List[Dict[str, Any]]] = None) -> Tuple[Dict[str, float], bool]:
    """
    Perform VIF analysis on the supplied logs (or load them from the default
    processed directory if ``logs`` is ``None``).  Returns a tuple containing
    the VIF results and a boolean indicating whether any VIF exceeds the
    ``VIF_THRESHOLD``.
    """
    if logs is None:
        processed_dir = Path("data/processed")
        logs = load_processed_logs(processed_dir)

    # Keep only valid logs
    logs = filter_invalid_workflows_from_logs(logs)

    # Extract numeric features for VIF – here we use ``depth`` and
    # ``complexity`` if present.
    depths = np.array([log.get("depth", 0) for log in logs], dtype=float)
    complexities = np.array([log.get("complexity", 0) for log in logs], dtype=float)

    vif_results = calculate_vif([depths, complexities])
    exceeded = any(v > VIF_THRESHOLD for v in vif_results.values())
    return vif_results, exceeded

def save_vif_report(report: Dict[str, Any], output_path: Path) -> Path:
    """
    Persist the VIF analysis report to ``output_path`` and return the path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    return output_path

def main():
    """
    CLI entry point – runs VIF analysis on the processed logs and writes a
    JSON report to ``data/results/vif_report.json``.
    """
    logs = load_processed_logs(Path("data/processed"))
    vif_results, exceeded = run_vif_analysis(logs)

    report = {
        "metric_name": "VIF",
        "threshold": VIF_THRESHOLD,
        "exceeded_threshold": exceeded,
        "values": vif_results,
    }

    output_path = Path("data/results/vif_report.json")
    save_vif_report(report, output_path)
    print(f"VIF report written to {output_path}")

if __name__ == "__main__":
    main()
