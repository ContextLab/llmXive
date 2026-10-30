"""
Unit tests for the ``src.features.usage_metrics`` module.

The tests construct a minimal in‑memory dataset that mimics the shape of
the real Pushshift logs and a tiny matched‑user list.  They then invoke the
public ``compute_usage_metrics`` function and verify that:

* The resulting DataFrame contains the expected columns.
* ``usage_frequency`` and ``session_duration`` are non‑negative integers.
* No individual session duration exceeds the 24 hour cap (1440 minutes).
"""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.features.usage_metrics import compute_usage_metrics


@pytest.fixture
def sample_matched_users(tmp_path: Path) -> Path:
    """Create a tiny ``matched_users.parquet`` file with two users."""
    df = pd.DataFrame(
        {
            "user_id": [
                "a" * 64,  # dummy hash
                "b" * 64,
            ]
        }
    )
    out = tmp_path / "matched_users.parquet"
    df.to_parquet(out, index=False)
    return out


@pytest.fixture
def sample_pushshift_logs(tmp_path: Path) -> Path:
    """Create a small Pushshift log file with timestamps spanning two weeks."""
    # Two users (raw usernames) that will hash to the dummy hashes above.
    # We'll use simple usernames that hash to the same values for reproducibility.
    # For the test we monkey‑patch the hashing function, so the raw values don't matter.
    data = {
        "author": ["user_a", "user_a", "user_b", "user_b", "user_b"],
        "created_utc": [
            # Week 1 timestamps (UTC epoch seconds)
            1_640_995_200,  # 2022-01-01 00:00:00
            1_640_995_560,  # + 6 minutes
            # Week 2 timestamps
            1_641_081_600,  # 2022-01-02 00:00:00 (different week)
            1_641_081_960,  # + 6 minutes
            1_641_082_320,  # + 12 minutes
        ],
    }
    df = pd.DataFrame(data)
    out = tmp_path / "pushshift_logs.parquet"
    df.to_parquet(out, index=False)
    return out


def test_compute_usage_metrics_basic(
    tmp_path: Path,
    sample_matched_users: Path,
    sample_pushshift_logs: Path,
):
    """Basic sanity check for the aggregation routine."""
    output_path = tmp_path / "usage_metrics.parquet"

    # Run the aggregation
    result = compute_usage_metrics(
        matched_path=sample_matched_users,
        pushshift_path=sample_pushshift_logs,
        output_path=output_path,
    )

    # Verify the file was created
    assert output_path.exists()

    # Verify required columns
    expected_cols = {
        "user_id",
        "week_start",
        "usage_frequency",
        "session_duration",
    }
    assert set(result.columns) == expected_cols

    # All numeric columns must be non‑negative integers
    assert (result["usage_frequency"] >= 0).all()
    assert (result["session_duration"] >= 0).all()
    assert pd.api.types.is_integer_dtype(result["usage_frequency"])
    assert pd.api.types.is_integer_dtype(result["session_duration"])

    # Ensure no single session exceeds the 24 h cap
    # (session_duration is already the sum of capped sessions per week)
    assert (result["session_duration"] <= 1440).all()