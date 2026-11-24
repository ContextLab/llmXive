"""
Unit test for the ``fetch_real_vr.py`` script.

The test verifies that the script raises ``RealDataUnavailableError`` when the
HuggingFace dataset cannot be accessed (e.g., by providing an invalid dataset
identifier). It also checks that a successful fetch writes a Parquet file.

NOTE: The test is deliberately lightweight and does not depend on network
connectivity for the success path – it monkey‑patches ``datasets.load_dataset``
with a dummy in‑memory dataset to simulate a successful download. This approach
satisfies the requirement that the script *must* attempt a real fetch while still
allowing the CI to run offline.
"""
import builtins
import io
import os
from pathlib import Path
from unittest import mock

import pytest
import pandas as pd

from code.data.fetch_real_vr import fetch_real_vr_logs, RealDataUnavailableError
from code.config import get_path

# ----------------------------------------------------------------------
# Helper: a minimal in‑memory HuggingFace dataset mock
# ----------------------------------------------------------------------
class DummyDataset:
    """Mimics a HuggingFace Dataset with a single ``to_pandas`` method."""
    def __init__(self, data):
        self._data = data

    def to_pandas(self):
        return pd.DataFrame(self._data)

class DummyDatasetDict(dict):
    """Mimics the ``DatasetDict`` returned by ``load_dataset``."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

# ----------------------------------------------------------------------
# Test: successful fetch (mocked)
# ----------------------------------------------------------------------
def test_fetch_real_vr_success(tmp_path):
    # Prepare dummy data
    dummy_data = {
        "response_time": [1.2, 2.3],
        "gaze_metrics": [0.45, 0.67],
        "judgment_rating": [0.8, 0.4],
        "participant_id": [1, 2],
        "story_id": [101, 102],
    }
    dummy_dataset = DummyDatasetDict(train=DummyDataset(dummy_data))

    with mock.patch("code.data.fetch_real_vr.load_dataset", return_value=dummy_dataset):
        # Use a temporary output location
        out_path = tmp_path / "vr_logs.parquet"
        result_path = fetch_real_vr_logs(out_path)

        # Verify the file exists and contains the expected columns
        assert result_path == out_path
        assert result_path.exists()
        df = pd.read_parquet(result_path)
        assert set(df.columns) == set(dummy_data.keys())
        assert len(df) == len(dummy_data["response_time"])

# ----------------------------------------------------------------------
# Test: fetch failure raises the correct custom exception
# ----------------------------------------------------------------------
def test_fetch_real_vr_failure():
    with mock.patch("code.data.fetch_real_vr.load_dataset", side_effect=RuntimeError("network down")):
        with pytest.raises(RealDataUnavailableError) as excinfo:
            fetch_real_vr_logs()

        # Ensure the message matches the spec exactly
        assert str(excinfo.value) == "FR-006 Violation: Real VR logs missing. Fetch failed."