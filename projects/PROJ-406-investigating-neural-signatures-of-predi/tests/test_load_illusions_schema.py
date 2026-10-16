"""Unit tests for the schema-mapping and aggregation helpers in
``src.ingest.load_illusions`` (no network access required)."""

import pandas as pd
import pytest

from src.ingest.load_illusions import (
    PONZO_REQUIRED_COLUMNS,
    _aggregate_per_subject,
    _map_columns,
)


def test_map_columns_exact_names():
    df = pd.DataFrame({
        "subject_id": ["s1"],
        "trial_id": [1],
        "arrow_angle": [45.0],
        "depth_cue": [1.0],
        "perceived_length": [110.0],
    })
    out = _map_columns(df, PONZO_REQUIRED_COLUMNS)
    assert list(out.columns) == PONZO_REQUIRED_COLUMNS


def test_map_columns_aliases():
    df = pd.DataFrame({
        "participant": ["s1", "s2"],
        "trial": [1, 2],
        "angle": [30.0, 45.0],
        "context": [0.5, 0.7],
        "response": [105.0, 112.0],
    })
    out = _map_columns(df, PONZO_REQUIRED_COLUMNS)
    assert set(PONZO_REQUIRED_COLUMNS).issubset(out.columns)


def test_map_columns_missing_raises():
    df = pd.DataFrame({"participant": ["s1"], "response": [100.0]})
    with pytest.raises(KeyError):
        _map_columns(df, PONZO_REQUIRED_COLUMNS)


def test_aggregate_per_subject_collapses_trials():
    df = pd.DataFrame({
        "subject_id": ["s1", "s1", "s2"],
        "trial_id": [1, 2, 1],
        "arrow_angle": [30.0, 60.0, 45.0],
        "depth_cue": [0.5, 0.5, 0.9],
        "perceived_length": [100.0, 120.0, 110.0],
    })
    out = _aggregate_per_subject(df)
    assert out["subject_id"].is_unique
    assert len(out) == 2
    s1 = out[out["subject_id"] == "s1"].iloc[0]
    assert s1["perceived_length"] == pytest.approx(110.0)
    assert s1["arrow_angle"] == pytest.approx(45.0)
    assert s1["trial_id"] == 2  # trial count


def test_aggregate_per_subject_unique_passthrough():
    df = pd.DataFrame({
        "subject_id": ["s1", "s2"],
        "trial_id": [1, 1],
        "arrow_angle": [30.0, 45.0],
        "depth_cue": [0.5, 0.9],
        "perceived_length": [100.0, 110.0],
    })
    out = _aggregate_per_subject(df)
    pd.testing.assert_frame_equal(out, df)