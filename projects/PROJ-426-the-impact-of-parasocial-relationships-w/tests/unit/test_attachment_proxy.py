"""
Unit tests for the attachment‑proxy feature (task T009).

The tests create a minimal in‑memory dataset, write the required input
files to temporary locations, invoke the ``compute_attachment_scores``
function, and then verify that:

* All retained users have scores in the range [0, 1].
* The number of excluded users matches the expectation based on the
  deliberately malformed baseline entries.
"""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.features.attachment_proxy import compute_attachment_scores


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory that mimics the project data layout."""
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        # Create required sub‑folders
        (base / "processed").mkdir(parents=True, exist_ok=True)
        (base / "lexicons").mkdir(parents=True, exist_ok=True)
        (base / "config").mkdir(parents=True, exist_ok=True)
        yield base


def write_lexicon(path: Path):
    """Write a tiny ECAR lexicon CSV."""
    df = pd.DataFrame(
        {
            "keyword": ["fear", "avoid", "trust"],
            "anxiety_weight": [1.0, 0.0, 0.0],
            "avoidance_weight": [0.0, 1.0, 0.0],
        }
    )
    df.to_csv(path, index=False)


def write_config(path: Path):
    """Write a baseline window config with 30 days."""
    path.write_text("baseline_days_preceding: 30\n", encoding="utf-8")


def write_matched(path: Path):
    """Write a minimal matched_users parquet file."""
    df = pd.DataFrame(
        {
            "user_id": [
                "a" * 64,
                "b" * 64,
                "c" * 64,
                "d" * 64,
            ],
            "baseline_text": [
                "fear trust",          # both anxiety and avoidance zero -> scores 0.5/2 tokens = 0.5? actually anxiety weight 1, avoidance 0 -> 0.5 anxiety, 0 avoidance
                "",                    # empty baseline – should be excluded
                "avoid unknown",      # contains avoidance keyword
                None,                  # None baseline – should be excluded
            ],
            "timestamp": [
                "2023-01-15T12:00:00Z",
                "2023-01-15T12:00:00Z",
                "2023-01-15T12:00:00Z",
                "2023-01-15T12:00:00Z",
            ],
        }
    )
    df.to_parquet(path, index=False)


def test_attachment_scores_basic(temp_data_dir):
    """Basic functionality test."""
    # Arrange: write required inputs
    lexicon_path = temp_data_dir / "lexicons" / "ecar_lexicon.csv"
    config_path = temp_data_dir / "config" / "baseline_window_config.yaml"
    matched_path = temp_data_dir / "processed" / "matched_users.parquet"
    output_path = temp_data_dir / "processed" / "attachment_scores.parquet"

    write_lexicon(lexicon_path)
    write_config(config_path)
    write_matched(matched_path)

    # Act
    result_df = compute_attachment_scores(
        matched_path=matched_path,
        lexicon_path=lexicon_path,
        config_path=config_path,
        output_path=output_path,
    )

    # Assert: output file exists
    assert output_path.exists()

    # The result should contain two users (the ones with non‑empty baseline)
    assert len(result_df) == 2

    # All scores must be within [0, 1]
    for _, row in result_df.iterrows():
        assert 0.0 <= row["attachment_anxiety_score"] <= 1.0
        assert 0.0 <= row["attachment_avoidance_score"] <= 1.0

    # Verify specific numeric expectations for the crafted rows
    # User a…a: text = "fear trust" → anxiety weight 1 (fear) over 2 tokens = 0.5,
    # avoidance weight 0 → 0.0
    user_a = result_df[result_df["user_id"] == "a" * 64].iloc[0]
    assert pytest.approx(user_a["attachment_anxiety_score"], rel=1e-3) == 0.5
    assert pytest.approx(user_a["attachment_avoidance_score"], rel=1e-3) == 0.0

    # User c…c: text = "avoid unknown" → anxiety 0, avoidance 1 over 2 tokens = 0.5
    user_c = result_df[result_df["user_id"] == "c" * 64].iloc[0]
    assert pytest.approx(user_c["attachment_anxiety_score"], rel=1e-3) == 0.0
    assert pytest.approx(user_c["attachment_avoidance_score"], rel=1e-3) == 0.5

    # Excluded user count should be stored in the DataFrame attrs
    assert result_df.attrs.get("excluded_user_count") == 2