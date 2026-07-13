"""Unit tests for the correlation analysis utilities.

These tests verify that the core functions behave correctly on small,
synthetic dataframes.  They do **not** depend on the heavy data‑loading
pipeline and therefore run quickly in CI.
"""

from __future__ import annotations

import pandas as pd

from correlation_analysis import (
    compute_spearman_correlation,
    save_correlation_results,
)
from pathlib import Path
import csv
import os

def test_compute_spearman_correlation_basic():
    # Simple monotonic relationship: perfect positive correlation
    x = pd.Series([1, 2, 3, 4, 5])
    y = pd.Series([10, 20, 30, 40, 50])
    corr, pval = compute_spearman_correlation(x, y)
    assert round(corr, 5) == 1.0
    assert pval < 0.01

def test_compute_spearman_correlation_nan_handling():
    x = pd.Series([1, 2, None, 4])
    y = pd.Series([10, None, 30, 40])
    corr, pval = compute_spearman_correlation(x, y)
    # After dropping NaNs we have two points (1,10) and (4,40) → perfect corr
    assert round(corr, 5) == 1.0

def test_save_correlation_results_creates_file(tmp_path: Path):
    output_file = tmp_path / "correlation_results.csv"
    results = [
        ("clone_density", "perplexity", 0.42, 0.001, 123),
        ("clone_density", "pass@1_accuracy", -0.15, 0.45, 123),
    ]
    # Call the function with an explicit path
    save_correlation_results(results, output_path=output_file)

    # Verify file exists and contents match expectations
    assert output_file.is_file()
    with output_file.open(newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    # Header + two data rows
    assert rows[0] == ["metric_x", "metric_y", "spearman", "p_value", "n_samples"]
    assert rows[1] == ["clone_density", "perplexity", "0.42", "0.001", "123"]
    assert rows[2] == ["clone_density", "pass@1_accuracy", "-0.15", "0.45", "123"]