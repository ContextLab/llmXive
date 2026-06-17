"""
Unit tests for the data validator (T016).

The tests exercise the core validation logic without touching the file‑system
and verify that the pass‑rate and flag counts meet the thresholds described in
the task specification.
"""

from __future__ import annotations

import pandas as pd
import pytest

from data.validator import (
    MissingInvariantFlag,
    DataQualityFlag,
    apply_missing_and_quality_flags,
)


@pytest.fixture
def sample_dataframe():
    """Create a small dataframe with a mixture of good and bad records."""
    data = {
        "name": ["K1", "K2", "K3", "K4"],
        # K1 – all good
        "crossing_number": [3, None, "5a", 7],
        # K2 – missing crossing_number
        "braid_index": [2, 3, "bad", 2],
        # K3 – format error in braid_index
        "volume": [1.2, 2.3, None, "not_a_float"],
        # K4 – missing volume + format error in volume
    }
    return pd.DataFrame(data)


def test_missing_and_format_flags(sample_dataframe):
    result = apply_missing_and_quality_flags(sample_dataframe)

    # Expect exactly one missing crossing_number (record 1) and one missing volume (record 2)
    missing_crossing = [
        f for f in result.null_flags if f["flag"] == MissingInvariantFlag.MISSING_CROSSING_NUMBER.name
    ]
    missing_volume = [
        f for f in result.null_flags if f["flag"] == MissingInvariantFlag.MISSING_VOLUME.name
    ]
    assert len(missing_crossing) == 1
    assert len(missing_volume) == 1

    # Format errors: crossing_number "5a", braid_index "bad", volume "not_a_float"
    format_crossing = [
        f for f in result.format_flags if f["flag"] == DataQualityFlag.FORMAT_ERROR_CROSSING_NUMBER.name
    ]
    format_braid = [
        f for f in result.format_flags if f["flag"] == DataQualityFlag.FORMAT_ERROR_BRAID_INDEX.name
    ]
    format_volume = [
        f for f in result.format_flags if f["flag"] == DataQualityFlag.FORMAT_ERROR_VOLUME.name
    ]
    assert len(format_crossing) == 1
    assert len(format_braid) == 1
    assert len(format_volume) == 1

    # No duplicates in this tiny set
    assert result.duplicate_records == []

    # Pass rate: total 4 records, 5 records flagged (some records have multiple flags)
    # Records with *any* flag: 4 (all rows have at least one issue)
    assert result.pass_rate == 0.0


def test_pass_rate_high_when_data_is_clean():
    df = pd.DataFrame(
        {
            "name": ["K1", "K2"],
            "crossing_number": [3, 4],
            "braid_index": [2, 2],
            "volume": [1.0, 2.5],
        }
    )
    result = apply_missing_and_quality_flags(df)
    assert result.pass_rate == 1.0
    assert result.null_flags == []
    assert result.format_flags == []
    assert result.duplicate_records == []