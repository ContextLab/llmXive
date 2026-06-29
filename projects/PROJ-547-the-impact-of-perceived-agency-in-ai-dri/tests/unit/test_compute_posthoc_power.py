"""
Unit test for the post‑hoc power computation script.

The test creates a minimal regression summary CSV with two rows:
- One with a reasonably large effect size, expected to yield power > 0.80.
- One with a tiny effect size, expected to yield power < 0.80, triggering a warning.

The script is executed via its ``compute_posthoc_power`` function, and the
resulting CSV is inspected for the presence of the ``power`` column and
correct row counts.
"""

from __future__ import annotations

import csv
import io
import sys
from pathlib import Path

import pandas as pd
import pytest

# Import the function under test
from analysis.compute_posthoc_power import compute_posthoc_power

@pytest.fixture
def temp_summary(tmp_path: Path) -> Path:
    """
    Create a temporary regression summary CSV with the minimal required columns.
    """
    summary_path = tmp_path / "regression_summary.csv"
    rows = [
        {
            "model_name": "high_power_model",
            "model_type": "linear",
            "effect_size": 0.4,  # Cohen's f² – should give high power
            "df_num": 2,
            "df_denom": 100,
            "alpha": 0.05,
        },
        {
            "model_name": "low_power_model",
            "model_type": "linear",
            "effect_size": 0.01,  # Very small effect → low power
            "df_num": 2,
            "df_denom": 100,
            "alpha": 0.05,
        },
    ]

    # Write CSV
    with summary_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    return summary_path

def test_compute_posthoc_power_creates_output(tmp_path: Path, temp_summary: Path):
    output_path = tmp_path / "power_estimates.csv"

    # Run the power computation
    result_df = compute_posthoc_power(
        summary_path=temp_summary,
        output_path=output_path,
        power_threshold=0.80,
    )

    # Verify the output file exists
    assert output_path.is_file(), "Power estimates CSV was not created."

    # Verify the DataFrame has the expected columns
    assert "power" in result_df.columns, "Result does not contain a 'power' column."

    # Verify we have the same number of rows as the input
    assert len(result_df) == 2, "Unexpected number of rows in power output."

    # Ensure that one of the rows has power below the threshold
    low_power_rows = result_df[result_df["power"] < 0.80]
    assert not low_power_rows.empty, "Expected at least one low‑power row."

    # Ensure that the high‑power row has power >= 0.80
    high_power_row = result_df[result_df["model_name"] == "high_power_model"]
    assert not high_power_row.empty
    assert float(high_power_row["power"].iloc[0]) >= 0.80

    # Load the CSV back and compare to the returned DataFrame
    loaded = pd.read_csv(output_path)
    pd.testing.assert_frame_equal(loaded, result_df, check_dtype=False)