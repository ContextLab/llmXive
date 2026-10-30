"""
Extended unit tests for ``src.validation.validate_match``.

The original test suite only exercised the basic success/failure
paths.  These additional tests verify that the new longitudinal‑depth
and power‑analysis logic behaves as expected.
"""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch

# Import the function under test.
from src.validation.validate_match import (
    validate_match,
    MIN_MATCHED_USERS,
    MIN_MATCH_RATE,
)


@pytest.fixture
def temp_dirs(tmp_path_factory):
    """
    Create a temporary project‑like directory layout containing the
    required ``data`` sub‑folders.
    """
    root = tmp_path_factory.mktemp("project_root")
    (root / "data" / "raw").mkdir(parents=True)
    (root / "data" / "processed").mkdir(parents=True)
    (root / "data" / "validation").mkdir(parents=True)
    return root


def _write_parquet(df: pd.DataFrame, path: Path):
    """Helper to write a DataFrame to Parquet."""
    df.to_parquet(path)


def test_successful_validation_with_longitudinal_depth_and_power(
    temp_dirs,
):
    """
    End‑to‑end success case:

    * 1000 loneliness users.
    * 900 matched users (90 % match rate).
    * Every matched user has ≥ 6 distinct months of data.
    * Detectable d should be ≤ 0.8 (no warning).
    """
    # ------------------------------------------------------------------
    # Create mock loneliness data (the raw dataset is not used by the
    # validation beyond counting rows, but we include a timestamp for
    # completeness).
    # ------------------------------------------------------------------
    loneliness_df = pd.DataFrame(
        {
            "user_id": [f"user_{i}" for i in range(1000)],
            "timestamp": pd.date_range(
                start="2022-01-01", periods=1000, freq="D"
            ),
        }
    )
    loneliness_path = (
        temp_dirs / "data" / "raw" / "loneliness_dataset.parquet"
    )
    _write_parquet(loneliness_df, loneliness_path)

    # ------------------------------------------------------------------
    # Matched users – each user has 6 months of observations.
    # ------------------------------------------------------------------
    rows = []
    for i in range(900):
        uid = f"user_{i}"
        # Create 6 months of data (one record per month).
        for month in range(6):
            rows.append(
                {
                    "user_id": uid,
                    "timestamp": pd.Timestamp(
                        f"2022-{month+1:02d}-15", tz="UTC"
                    ),
                    "UCLA_Loneliness_Score": 3.0,
                }
            )
    matched_df = pd.DataFrame(rows)
    matched_path = (
        temp_dirs / "data" / "processed" / "matched_users.parquet"
    )
    _write_parquet(matched_df, matched_path)

    # ------------------------------------------------------------------
    # Patch the global path constants so that the validation code reads
    # from our temporary layout.
    # ------------------------------------------------------------------
    with patch(
        "src.validation.validate_match.LONELINESS_USERS_PATH", loneliness_path
    ), patch(
        "src.validation.validate_match.MATCHED_USERS_PATH", matched_path
    ), patch(
        "src.validation.validate_match.OUTPUT_MATCH_REPORT_PATH",
        temp_dirs / "data" / "validation" / "match_report.yaml",
    ), patch(
        "src.validation.validate_match.OUTPUT_POWER_REPORT_PATH",
        temp_dirs / "data" / "validation" / "power_analysis_report.yaml",
    ):
        report = validate_match()

    # ------------------------------------------------------------------
    # Assertions on the returned report.
    # ------------------------------------------------------------------
    assert report["status"] == "pass"
    assert report["total_users"] == 1000
    assert report["matched_users"] == 900
    assert report["match_rate"] == pytest.approx(0.9)
    assert report["longitudinal_depth_pass"] is True
    # Detectable d for N=900 should be well below 0.8.
    assert report["detectable_d"] < 0.8

    # ------------------------------------------------------------------
    # Verify that both YAML files were written.
    # ------------------------------------------------------------------
    match_report_path = (
        temp_dirs / "data" / "validation" / "match_report.yaml"
    )
    power_report_path = (
        temp_dirs / "data" / "validation" / "power_analysis_report.yaml"
    )
    assert match_report_path.exists()
    assert power_report_path.exists()


def test_failure_due_to_insufficient_longitudinal_depth(temp_dirs):
    """
    The validation should fail when at least one matched user has
    fewer than six distinct months of data.
    """
    loneliness_df = pd.DataFrame(
        {
            "user_id": [f"user_{i}" for i in range(1000)],
            "timestamp": pd.date_range(
                start="2022-01-01", periods=1000, freq="D"
            ),
        }
    )
    _write_parquet(
        loneliness_df,
        temp_dirs / "data" / "raw" / "loneliness_dataset.parquet",
    )

    # Create matched users where the first user only has 3 months.
    rows = []
    for i in range(900):
        uid = f"user_{i}"
        months = 6 if i != 0 else 3  # user_0 is the problematic one
        for month in range(months):
            rows.append(
                {
                    "user_id": uid,
                    "timestamp": pd.Timestamp(
                        f"2022-{month+1:02d}-15", tz="UTC"
                    ),
                    "UCLA_Loneliness_Score": 3.0,
                }
            )
    matched_df = pd.DataFrame(rows)
    _write_parquet(
        matched_df,
        temp_dirs / "data" / "processed" / "matched_users.parquet",
    )

    with patch(
        "src.validation.validate_match.LONELINESS_USERS_PATH",
        temp_dirs / "data" / "raw" / "loneliness_dataset.parquet",
    ), patch(
        "src.validation.validate_match.MATCHED_USERS_PATH",
        temp_dirs / "data" / "processed" / "matched_users.parquet",
    ), patch(
        "src.validation.validate_match.OUTPUT_MATCH_REPORT_PATH",
        temp_dirs / "data" / "validation" / "match_report.yaml",
    ), patch(
        "src.validation.validate_match.OUTPUT_POWER_REPORT_PATH",
        temp_dirs / "data" / "validation" / "power_analysis_report.yaml",
    ), pytest.raises(RuntimeError) as excinfo:
        validate_match()

    # The error message must contain the longitudinal‑depth token.
    assert "Insufficient Longitudinal Depth" in str(excinfo.value)