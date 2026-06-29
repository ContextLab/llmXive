"""Unit tests for ``code/data/label_bug_fixes.py``."""

from __future__ import annotations

import pandas as pd
import pytest

# Import the function directly from the module under test
from data.label_bug_fixes import label_bug_fixes


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """Create a tiny DataFrame with representative commit messages."""
    return pd.DataFrame(
        {
            "commit_hash": [
                "a1b2c3",
                "d4e5f6",
                "112233",
                "445566",
            ],
            "message": [
                "Fix bug in parsing logic",      # should be bug‑fix
                "Add new feature for UI",        # not a bug‑fix
                "Patch: resolve issue #42",      # bug‑fix (contains 'patch' and 'resolve')
                "Refactor code, improve readability",  # not a bug‑fix
            ],
        }
    )


def test_label_bug_fixes_correctness(sample_dataframe: pd.DataFrame) -> None:
    """The function must add a ``bug_label`` column with the expected values."""
    result = label_bug_fixes(sample_dataframe)

    # The original DataFrame must be left untouched (function returns a copy)
    assert "bug_label" not in sample_dataframe.columns

    # Verify the new column exists and has the right length
    assert "bug_label" in result.columns
    assert len(result) == len(sample_dataframe)

    # Expected labels based on the simple keyword heuristic
    expected = [1, 0, 1, 0]
    assert result["bug_label"].tolist() == expected