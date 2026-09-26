"""
Unit tests for T017: Fetch Real CoT Traces.

These tests verify the "Fail Loudly" behavior of the loader.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.loaders import load_cot_traces, DataFetchError

class TestT017Loader:
    """Tests for the real data fetcher."""

    def test_load_cot_traces_success(self):
        """Test that load_cot_traces returns data when the fetch succeeds."""
        # Mock the load_dataset to return a mock dataset with data
        mock_ds = MagicMock()
        mock_ds.to_list.return_value = [
            {"task_id": "test-1", "interaction_type": "spatial", "steps": []}
        ]
        
        with patch('utils.loaders.load_dataset', return_value=mock_ds):
            result = load_cot_traces()
            assert len(result) == 1
            assert result[0]["task_id"] == "test-1"

    def test_load_cot_traces_empty_dataset_raises(self):
        """Test that an empty dataset raises DataFetchError."""
        mock_ds = MagicMock()
        mock_ds.to_list.return_value = []
        
        with patch('utils.loaders.load_dataset', return_value=mock_ds):
            with pytest.raises(DataFetchError, match="contains no records"):
                load_cot_traces()

    def test_load_cot_traces_fetch_failure_raises(self):
        """Test that a network failure raises DataFetchError."""
        with patch('utils.loaders.load_dataset', side_effect=Exception("404 Not Found")):
            with pytest.raises(DataFetchError, match="not found on HuggingFace Hub"):
                load_cot_traces()

    def test_load_cot_traces_general_failure_raises(self):
        """Test that a general failure raises DataFetchError."""
        with patch('utils.loaders.load_dataset', side_effect=Exception("Network Error")):
            with pytest.raises(DataFetchError, match="Failed to fetch dataset"):
                load_cot_traces()

    def test_no_synthetic_fallback(self):
        """
        Verify that the loader does NOT fall back to synthetic data.
        We check that the function structure does not contain 'synthetic' or 'mock' generation.
        """
        import inspect
        source = inspect.getsource(load_cot_traces)
        assert "generate_synthetic" not in source.lower()
        assert "np.random" not in source.lower()
        assert "mock_trace" not in source.lower()
        # Ensure it explicitly raises on failure
        assert "raise DataFetchError" in source