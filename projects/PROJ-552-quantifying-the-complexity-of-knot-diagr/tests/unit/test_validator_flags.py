"""
Unit tests for the flagging logic implemented in ``code/data/validator.py``.
"""

from __future__ import annotations

import pandas as pd

from data.validator import (
    MissingInvariantFlag,
    DataQualityFlag,
    apply_missing_and_quality_flags,
    validate_dataset_data_quality,
)


def test_missing_and_quality_flags_basic():
    # Create a tiny DataFrame with a mixture of good and bad rows.
    raw = pd.DataFrame(
        [
            {
                "knot_id": "4_1",
                "crossing_number": 4,
                "braid_index": 3,
                "hyperbolic_volume": 2.02988,
                "alternating": "alternating",
            },
            {
                "knot_id": "5_2",
                "crossing_number": None,  # missing crossing number
                "braid_index": 2,
                "hyperbolic_volume": -1.0,  # negative volume (quality issue)
                "alternating": "non-alternating",
            },
            {
                "knot_id": "6_1",
                "crossing_number": 6.5,  # non‑integer crossing
                "braid_index": "bad",   # non‑integer braid index
                "hyperbolic_volume": 3.5,
                "alternating": "maybe",  # unrecognised classification
            },
        ]
    )

    df_flagged = apply_missing_and_quality_flags(raw)

    # Row 0 – everything fine.
    assert df_flagged.loc[0, "missing_invariant_flags"] == []
    assert df_flagged.loc[0, "data_quality_flags"] == []

    # Row 1 – missing crossing number + negative volume.
    missing = df_flagged.loc[1, "missing_invariant_flags"]
    quality = df_flagged.loc[1, "data_quality_flags"]
    assert MissingInvariantFlag.MISSING_CROSSING_NUMBER in missing
    assert DataQualityFlag.NEGATIVE_VOLUME in quality

    # Row 2 – non‑integer crossing, non‑integer braid, unrecognised alternating.
    missing = df_flagged.loc[2, "missing_invariant_flags"]
    quality = df_flagged.loc[2, "data_quality_flags"]
    assert DataQualityFlag.NON_INTEGER_CROSSING in quality
    assert DataQualityFlag.NON_INTEGER_BRAID in quality
    assert DataQualityFlag.UNRECOGNIZED_ALTERNATING in quality

    # Validate the helper that returns ValidationResult objects.
    results = validate_dataset_data_quality(raw)
    assert len(results) == 3
    assert any(
        MissingInvariantFlag.MISSING_CROSSING_NUMBER in r.missing_flags for r in results
    )
    assert any(
        DataQualityFlag.NEGATIVE_VOLUME in r.quality_flags for r in results
    )
