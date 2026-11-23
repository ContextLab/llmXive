"""
Unit test for the deterministic matching verification script.

The test creates two temporary Parquet files with a minimal but
realistic schema, runs the verification function, and expects a
successful exit (i.e., no AssertionError). It also checks that
a deliberate nondeterministic modification raises an error.
"""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Import the verification function directly
from src.validation.verify_deterministic_match import (
    verify_deterministic_match,
    _normalize_dataframe,
)

@pytest.fixture
def sample_data(tmp_path: Path):
    """
    Create minimal loneliness and pushshift datasets.

    The loneliness dataset contains a `username` column (raw Reddit
    usernames) and a `baseline_text` column required by the matching
    logic. The pushshift dataset contains an `author_hash` column
    that matches the SHA‑256 hash of the usernames.
    """
    # Loneliness dataset
    loneliness_df = pd.DataFrame(
        {
            "username": ["userA", "userB", "userC"],
            "baseline_text": ["text A", "text B", "text C"],
        }
    )
    loneliness_path = tmp_path / "loneliness_dataset.parquet"
    loneliness_df.to_parquet(loneliness_path)

    # Pushshift dataset – author_hash must match hashed usernames
    from src.match.user_match import hash_username

    pushshift_df = pd.DataFrame(
        {
            "author_hash": [hash_username(u) for u in ["userA", "userB"]],
            "body": ["comment A", "comment B"],
        }
    )
    pushshift_path = tmp_path / "pushshift_logs.parquet"
    pushshift_df.to_parquet(pushshift_path)

    return loneliness_path, pushshift_path

def test_verify_deterministic_match_success(sample_data, monkeypatch):
    """
    The verification should pass when the data are deterministic.
    """
    loneliness_path, pushshift_path = sample_data

    # Patch the toolkit paths to point to our temporary files
    from llmxive_toolkit import paths

    monkeypatch.setattr(
        paths,
        "data",
        lambda *parts: Path(str(loneliness_path.parent.parent / Path(*parts))),
    )

    # Run verification – should not raise
    verify_deterministic_match()

def test_verify_deterministic_match_failure(sample_data, monkeypatch):
    """
    Introduce a nondeterministic change (shuffle rows) and ensure the
    verification raises an AssertionError.
    """
    loneliness_path, pushshift_path = sample_data

    # Patch paths as in the success test
    from llmxive_toolkit import paths

    monkeypatch.setattr(
        paths,
        "data",
        lambda *parts: Path(str(loneliness_path.parent.parent / Path(*parts))),
    )

    # Import the internal matching functions to manipulate the data
    from src.match import user_match

    # Monkey‑patch perform_matching to return a shuffled DataFrame on the
    # second call, simulating nondeterminism.
    original_perform = user_match.perform_matching

    call_count = {"cnt": 0}

    def flaky_perform(*args, **kwargs):
        result = original_perform(*args, **kwargs)
        call_count["cnt"] += 1
        if call_count["cnt"] == 2:
            # Shuffle rows to break determinism
            return result.sample(frac=1, random_state=42).reset_index(drop=True)
        return result

    monkeypatch.setattr(user_match, "perform_matching", flaky_perform)

    with pytest.raises(AssertionError, match="nondeterministic"):
        verify_deterministic_match()

def test_normalize_dataframe():
    """
    Ensure that the normalisation routine produces a deterministic
    ordering independent of the original row order.
    """
    df = pd.DataFrame(
        {
            "b": [2, 1],
            "a": ["y", "x"],
        }
    )
    normalized = _normalize_dataframe(df)
    # Columns should be sorted alphabetically
    assert list(normalized.columns) == ["a", "b"]
    # Rows should be sorted lexicographically by all columns
    assert normalized.iloc[0]["a"] == "x"
    assert normalized.iloc[1]["a"] == "y"