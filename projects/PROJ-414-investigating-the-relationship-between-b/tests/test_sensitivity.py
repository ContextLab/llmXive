"""Tests for the sensitivity analysis (T007)."""
import json
import os
from pathlib import Path

import pandas as pd
import pytest

from llmxive_toolkit import paths

# The summary CSV should exist after the sensitivity stage runs.
def test_summary_exists():
    summary_path = paths.results("sensitivity_summary.csv")
    assert summary_path.is_file(), "sensitivity_summary.csv not found"

def test_summary_structure():
    df = pd.read_csv(paths.results("sensitivity_summary.csv"))
    # Exactly six rows for the 3×2 parameter grid
    assert len(df) == 6, f"expected 6 rows, got {len(df)}"
    required_cols = {
        "window_seconds",
        "step_seconds",
        "descriptor_mean",
        "descriptor_sd",
        "descriptor_range",
        "correlation_sd",
    }
    assert required_cols.issubset(set(df.columns)), f"missing columns: {required_cols - set(df.columns)}"
    # If the association stage ran, correlation_sd should be numeric;
    # otherwise it must be the placeholder string.
    for val in df["correlation_sd"]:
        if isinstance(val, str):
            assert val == "not_computable_no_skill_proxy"
        else:
            # numeric value
            assert isinstance(val, (float, int))

# Ensure the sensitivity stage can be invoked via the orchestrator.
def test_run_all_sensitivity():
    # Run the orchestrator with only the sensitivity stage.
    # The orchestrator will invoke the sensitivity module which
    # internally re‑runs the connectivity and analysis stages.
    exit_code = os.system("python code/run_all.py --stage sensitivity")
    assert exit_code == 0, "run_all.py with --stage sensitivity failed"