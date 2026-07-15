"""
Additional specific contract tests for analysis_output.schema.yaml.
Focuses on numeric constraints and logical consistency.
"""
import json
import math
from pathlib import Path

import pytest

from utils.config import get_project_root

PROJECT_ROOT = get_project_root()
DATA_DIR = PROJECT_ROOT / "data" / "processed"

@pytest.mark.contract
def test_analysis_variance_non_negative():
    """
    Ensures variance values in the analysis output are non-negative.
    Variance cannot be negative by definition.
    """
    analysis_file = DATA_DIR / "analysis_results.json"
    if not analysis_file.exists():
        pytest.skip("Analysis output file not found.")

    with open(analysis_file, "r") as f:
        data = json.load(f)

    descriptors = data.get("descriptors", [])
    for i, record in enumerate(descriptors):
        for var_key in ["bond_variance", "angle_variance", "dihedral_variance"]:
            val = record.get(var_key)
            if val is not None:
                if math.isnan(val) or math.isinf(val):
                    raise AssertionError(
                        f"Record {i} has invalid {var_key}: {val} (NaN or Inf)"
                    )
                if val < 0:
                    raise AssertionError(
                        f"Record {i} has negative {var_key}: {val}"
                    )

@pytest.mark.contract
def test_analysis_correlation_range():
    """
    Ensures Pearson/Spearman coefficients are within [-1, 1].
    """
    analysis_file = DATA_DIR / "analysis_results.json"
    if not analysis_file.exists():
        pytest.skip("Analysis output file not found.")

    with open(analysis_file, "r") as f:
        data = json.load(f)

    correlations = data.get("correlations", {})
    for metric_name, metric_data in correlations.items():
        if isinstance(metric_data, dict):
            coef = metric_data.get("coefficient")
            if coef is not None:
                if not (-1.0 <= coef <= 1.0):
                    raise AssertionError(
                        f"Correlation coefficient for {metric_name} is out of range: {coef}"
                    )

@pytest.mark.contract
def test_analysis_p_value_range():
    """
    Ensures p-values are within [0, 1].
    """
    analysis_file = DATA_DIR / "analysis_results.json"
    if not analysis_file.exists():
        pytest.skip("Analysis output file not found.")

    with open(analysis_file, "r") as f:
        data = json.load(f)

    correlations = data.get("correlations", {})
    for metric_name, metric_data in correlations.items():
        if isinstance(metric_data, dict):
            p_val = metric_data.get("p_value")
            if p_val is not None:
                if not (0.0 <= p_val <= 1.0):
                    raise AssertionError(
                        f"P-value for {metric_name} is out of range: {p_val}"
                    )
            fdr_p = metric_data.get("fdr_corrected_p")
            if fdr_p is not None:
                if not (0.0 <= fdr_p <= 1.0):
                    raise AssertionError(
                        f"FDR-corrected P-value for {metric_name} is out of range: {fdr_p}"
                    )