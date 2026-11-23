"""
Integration test for the data completeness validation (T010).

This test verifies that the ``run_data_completeness_check`` function in
``code.data.preprocess`` raises a ``ValueError`` containing the exact phrase
``Data Completeness Error`` when the dataset completeness is below the
95 % threshold.
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import pandas as pd

# Ensure the repository root is on the import path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from code.data.preprocess import run_data_completeness_check

class MockDataset:
    """Simple mock returning a pandas DataFrame via ``to_pandas``."""
    def __init__(self, data):
        self._data = data
    
    def to_pandas(self):
        return pd.DataFrame(self._data)

def make_dataset(valid: int, invalid: int) -> MockDataset:
    """Create a mock dataset with ``valid`` complete rows and ``invalid`` rows missing a required field."""
    total = valid + invalid
    rows = []
    for i in range(valid):
        rows.append({
            "pr_id": f"PR-{i}",
            "diff": f"diff {i}",
            "review_comments": f"comment {i}",
            "merge_timestamp": "2023-01-01",
            "project_name": "sample-project"
        })
    for i in range(invalid):
        rows.append({
            "pr_id": f"PR-{valid + i}",
            "diff": None,  # Missing required field
            "review_comments": f"comment {valid + i}",
            "merge_timestamp": "2023-01-01",
            "project_name": "sample-project"
        })
    return MockDataset(rows)

def test_completeness_below_threshold_raises():
    """
    Dataset with 90 % completeness (10 % missing) should raise the
    ``Data Completeness Error``.
    """
    mock_data = make_dataset(valid=90, invalid=10)
    with patch("code.data.preprocess.fetch_dataset", return_value=mock_data.to_pandas()):
        with pytest.raises(ValueError) as excinfo:
            run_data_completeness_check()
        err_msg = str(excinfo.value).lower()
        assert "data completeness error" in err_msg
        # Ensure the message mentions the observed percentage (≈90)
        assert "90.00" in err_msg or "90" in err_msg

def test_completeness_at_threshold_passes():
    """
    Dataset with exactly 95 % completeness should **not** raise.
    """
    mock_data = make_dataset(valid=95, invalid=5)
    with patch("code.data.preprocess.fetch_dataset", return_value=mock_data.to_pandas()):
        # Should complete without exception
        run_data_completeness_check()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])