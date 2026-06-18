"""Unit tests for the data validator."""

from pathlib import Path

import pandas as pd
import pytest

from data.validator import apply_missing_and_quality_flags, ValidationResult


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Create a small DataFrame with intentional problems."""
    return pd.DataFrame(
        {
            "knot_id": ["3_1", "4_1", "5_1", "5_1"],  # duplicate on purpose
            "crossing_number": [3, 4, "five", 5],  # non‑int on row 2
            "braid_index": [2, 2.0, 3, 3],  # ok (float .0 accepted)
            "hyperbolic_volume": [0.0, 1.2, -0.5, 2.0],  # zero / negative problematic
            "alternating": ["alternating", "non-alternating", "maybe", "alternating"],
        }
    )


def test_apply_missing_and_quality_flags(sample_df):
    result: ValidationResult = apply_missing_and_quality_flags(sample_df)

    # Total records should be 4
    assert result.total_records == 4
    # One row has a null? (none in fixture) – expect 0
    assert result.null_records == 0
    # Expect format errors on crossing_number (row 2) and volume (rows 1 & 3)
    # → 3 errors total
    assert result.format_errors == 3
    # One duplicate row (index 3 repeats row 2)
    assert result.duplicate_records == 1
    # Flags list should contain the relevant enums
    flag_names = {str(f) for f in result.flags}
    assert "non_integer_crossing_number" in flag_names
    assert "non_positive_hyperbolic_volume" in flag_names
    assert "invalid_alternating_classification" in flag_names