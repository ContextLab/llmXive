"""
Unit tests for ``src.lib.utils``.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.lib.utils import (
    set_seed,
    load_json,
    save_json,
    load_csv,
    save_csv,
    setup_logging,
)


def test_set_seed_reproducibility():
    """Calling ``set_seed`` twice with the same seed must produce identical RNG output."""
    set_seed(123)
    a = np.random.rand()
    set_seed(123)
    b = np.random.rand()
    assert a == b, "NumPy RNG not deterministic after reseeding"


def test_json_io_roundtrip(tmp_path: Path):
    """Saving and loading JSON must preserve data with deterministic ordering."""
    data = {"b": 2, "a": 1, "nested": {"z": 0, "y": 1}}
    file_path = tmp_path / "test.json"
    save_json(data, file_path)

    # The file must exist and be valid JSON
    assert file_path.is_file()
    with file_path.open() as f:
        raw = f.read()
    # The JSON dump should be sorted by keys
    loaded = json.loads(raw)
    assert list(loaded.keys()) == ["a", "b", "nested"]

    # Loading via helper should return the same dict
    roundtrip = load_json(file_path)
    assert roundtrip == data


def test_csv_io_roundtrip(tmp_path: Path):
    """Saving and loading CSV must preserve data."""
    df_original = pd.DataFrame({"col1": [1, 2, 3], "col2": ["x", "y", "z"]})
    file_path = tmp_path / "test.csv"
    save_csv(df_original, file_path)

    assert file_path.is_file()
    df_loaded = load_csv(file_path)
    pd.testing.assert_frame_equal(df_loaded, df_original)


def test_setup_logging():
    """Calling ``setup_logging`` should configure the root logger."""
    logger = setup_logging()
    # The logger returned should be the root logger
    assert logger is logging.getLogger()
    # Ensure the logger has at least one handler after setup
    assert logger.handlers, "Root logger has no handlers after setup_logging()"