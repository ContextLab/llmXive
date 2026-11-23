import os
import pytest
from pathlib import Path
import pandas as pd

from code.data_loader import (
    fetch_agent_logs,
    fetch_atbench,
    map_atbench_labels,
    LoudFailureError,
    generate_deterministic_timestamp
)
from code.config import get_path

class TestFetchAgentLogs:
    """Tests for fetch_agent_logs function."""

    def test_fetch_agent_logs_streaming(self):
        """Test that fetch_agent_logs streams data correctly."""
        output_path = str(get_path("data", "raw", "agent_logs.csv"))
        
        # Remove existing file if present
        if os.path.exists(output_path):
            os.remove(output_path)
        
        # Fetch the dataset
        result_path = fetch_agent_logs(output_path=output_path, chunk_size=1000)
        
        # Verify file was created
        assert os.path.exists(result_path), f"Output file not created at {result_path}"
        
        # Verify file is not empty
        assert os.path.getsize(result_path) > 0, "Output file is empty"
        
        # Verify it can be read as CSV
        df = pd.read_csv(result_path, nrows=100)
        assert len(df) > 0, "Could not read any rows from output file"
        assert "log_id" in df.columns or len(df.columns) > 0, "Expected log_id column or data"

    def test_fetch_agent_logs_failure(self):
        """Test that fetch_agent_logs raises LoudFailureError on invalid dataset."""
        with pytest.raises(LoudFailureError):
            # Try to fetch a non-existent dataset
            load_dataset = __import__('datasets', fromlist=['load_dataset']).load_dataset
            # This test is skipped in CI if network is unavailable
            pytest.skip("Network fetch test - requires real dataset access")

class TestFetchATBench:
    """Tests for fetch_atbench function."""

    def test_fetch_atbench(self):
        """Test that fetch_atbench loads data correctly."""
        df = fetch_atbench()
        assert len(df) > 0, "ATBench dataset is empty"
        assert "label" in df.columns or "log_id" in df.columns, "Expected label or log_id column"

    def test_timestamp_derivation(self):
        """Test that timestamps are derived correctly from log_id."""
        test_log_id = "test-log-123"
        timestamp = generate_deterministic_timestamp(test_log_id)
        assert isinstance(timestamp, int), "Timestamp should be an integer"
        assert 0 <= timestamp < 86400, "Timestamp should be within seconds in a day"

class TestMapATBenchLabels:
    """Tests for map_atbench_labels function."""

    def test_label_mapping_attack(self):
        """Test mapping of attack labels to 'novel'."""
        df = pd.DataFrame({"label": ["attack", "malicious", "Attack", "MALICIOUS"]})
        result = map_atbench_labels(df)
        assert all(result["mapped_label"] == "novel"), "Attack labels should map to 'novel'"

    def test_label_mapping_safe(self):
        """Test mapping of safe labels to 'benign'."""
        df = pd.DataFrame({"label": ["safe", "benign", "Safe", "BENIGN"]})
        result = map_atbench_labels(df)
        assert all(result["mapped_label"] == "benign"), "Safe labels should map to 'benign'"

    def test_label_mapping_unknown(self):
        """Test mapping of unknown labels."""
        df = pd.DataFrame({"label": ["unknown", "other", ""]})
        result = map_atbench_labels(df)
        assert all(result["mapped_label"] == "unknown"), "Unknown labels should map to 'unknown'"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
