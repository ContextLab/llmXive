"""
Unit test for T008 – outlier detection and Z‑score normalization.
The test creates a minimal CSV with two conditions, runs the preprocessing
pipeline in file‑mode, and checks that:
  * an ``is_outlier`` column is present,
  * outliers are correctly flagged based on the IQR rule,
  * the reaction‑time column is Z‑score normalized (mean≈0, std≈1) within each condition.
"""

import os
import pandas as pd
import numpy as np
import tempfile
import json
import pytest

# Ensure the code directory is on the import path
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2] / "code"
sys.path.insert(0, str(PROJECT_ROOT))

from preprocess import run_preprocessing, _detect_column

def create_sample_csv(path: Path):
    """
    Write a CSV with two conditions. The second condition contains an outlier
    that should be flagged by the IQR rule.
    """
    df = pd.DataFrame({
        "participant_id": ["sub-001", "sub-002", "sub-003", "sub-004"],
        "condition": ["rejection", "rejection", "control", "control"],
        # reaction times: control has an extreme high value (outlier)
        "reaction_time": [500, 520, 450, 900],
        "mood_rating": [3, 4, 2, 5]
    })
    df.to_csv(path, index=False)

def test_t008_preprocessing(tmp_path):
    # Arrange
    input_csv = tmp_path / "sample.csv"
    output_csv = tmp_path / "preprocessed.csv"
    create_sample_csv(input_csv)

    # Act
    run_preprocessing(str(input_csv), str(output_csv), design_type="Within-Subjects")

    # Assert output file exists
    assert output_csv.is_file(), "Preprocessed CSV was not created"

    # Load processed data
    df_out = pd.read_csv(output_csv)

    # Determine the reaction‑time column name used after cleaning
    rt_col = _detect_column(df_out, ["Reaction Time", "reaction_time", "rt"])
    condition_col = _detect_column(df_out, ["Condition", "condition"])

    # 1. ``is_outlier`` column must exist and be boolean
    assert "is_outlier" in df_out.columns, "Missing 'is_outlier' column"
    assert df_out["is_outlier"].dtype == bool or set(df_out["is_outlier"].unique()).issubset({0, 1, True, False})

    # 2. The outlier (reaction_time = 900 in 'control') should be flagged
    outlier_row = df_out[(df_out[condition_col] == "control") & (df_out[rt_col] > 0)]
    # After Z‑score, the extreme value will have a large positive z; we check the flag
    assert outlier_row["is_outlier"].iloc[0] is True, "Outlier was not flagged"

    # 3. Verify Z‑score normalization per condition
    for cond in df_out[condition_col].unique():
        group = df_out[df_out[condition_col] == cond][rt_col]
        mean = np.mean(group)
        std = np.std(group, ddof=0)  # population std matches pandas default std(ddof=1) after transform
        # Allow small numerical tolerance
        assert abs(mean) < 1e-6, f"Mean of normalized RT not close to 0 for condition {cond}"
        # When only two non‑outlier points exist the std may be 0; in that case the
        # implementation sets all values to 0, which is acceptable.
        if len(group) > 1:
            assert abs(std - 1.0) < 1e-6, f"Std of normalized RT not close to 1 for condition {cond}"