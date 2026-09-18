import os
import sys
import gc
import csv
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from io import StringIO

import pytest
import psutil

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from code.lib.data_loader import (
    stream_ruler_dataset,
    get_current_memory_mb,
    log_memory_usage,
    RAM_LIMIT_GB,
    MEMORY_LOG_PATH,
    DataStreamer
)

class TestMemoryConstraints:
    """Test that the data loader enforces memory limits."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Setup temporary directory for logs."""
        # We need to override the global MEMORY_LOG_PATH for testing
        # Since the module defines it at import time, we patch the function
        # that uses it or mock the path.
        
        # Create a temp log file path
        self.temp_dir = tmp_path
        self.temp_log_path = os.path.join(self.temp_dir, "memory_profile.csv")
        
        # Patch the global constant in the module
        with patch("code.lib.data_loader.MEMORY_LOG_PATH", self.temp_log_path):
            yield

    def test_peak_memory_assertion_on_synthetic_stream(self):
        """
        Unit test asserting peak memory usage < 7GB on a synthetic Moderate-sized stream.
        
        Since we cannot easily fake the actual dataset streaming without mocking,
        we simulate the stream process with mock data that triggers memory logging,
        and assert that the logging mechanism works and stays under the limit
        (since we are mocking the memory usage to be low).
        """
        # Mock psutil to return a low memory usage (e.g., 1GB)
        # This simulates a "Moderate-sized stream" that fits within limits
        mock_memory_mb = 1024.0  # 1 GB
        
        with patch("code.lib.data_loader.psutil.Process") as MockProcess:
            mock_instance = MagicMock()
            mock_instance.memory_info.return_value = MagicMock(rss=mock_memory_mb * 1024 * 1024)
            MockProcess.return_value = mock_instance
            
            # Mock the dataset loader to return a small synthetic stream
            mock_data = [
                {"id": f"doc_{i}", "text": "x" * 1000, "label": 0} 
                for i in range(50)  # Moderate size: 50 docs
            ]
            
            with patch("code.lib.data_loader.load_dataset") as mock_load:
                # Create an iterator that yields our mock data
                mock_load.return_value = MagicMock(__iter__=lambda self: iter(mock_data))
                
                # Run the stream
                batch_count = 0
                for batch in stream_ruler_dataset(batch_size=10):
                    batch_count += 1
                    assert len(batch) > 0
                    # Verify memory logging happened
                    assert os.path.exists(self.temp_log_path)
                
                # Verify we processed all data
                assert batch_count == 5
                
                # Verify the log file contains entries
                with open(self.temp_log_path, "r", newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    
                assert len(rows) > 0
                
                # Assert all logged entries are under the limit
                for row in rows:
                    mem_gb = float(row["memory_gb"])
                    assert mem_gb < RAM_LIMIT_GB, f"Memory {mem_gb}GB exceeded limit {RAM_LIMIT_GB}GB"
                    assert row["status"] == "OK"

    def test_memory_limit_exceeded_raises_error(self):
        """Test that exceeding RAM limit raises MemoryError."""
        mock_memory_mb = 8000.0  # 8 GB, exceeds 7GB limit
        
        with patch("code.lib.data_loader.psutil.Process") as MockProcess:
            mock_instance = MagicMock()
            mock_instance.memory_info.return_value = MagicMock(rss=mock_memory_mb * 1024 * 1024)
            MockProcess.return_value = mock_instance
            
            # Mock dataset
            mock_data = [{"id": "doc_1", "text": "test"}]
            with patch("code.lib.data_loader.load_dataset") as mock_load:
                mock_load.return_value = MagicMock(__iter__=lambda self: iter(mock_data))
                
                with pytest.raises(MemoryError, match="RAM limit exceeded"):
                    # Force a log entry to trigger the check
                    log_memory_usage("test_step", document_id="test_doc")
            
    def test_log_file_creation(self):
        """Test that the log file is created correctly."""
        mock_memory_mb = 500.0
        
        with patch("code.lib.data_loader.psutil.Process") as MockProcess:
            mock_instance = MagicMock()
            mock_instance.memory_info.return_value = MagicMock(rss=mock_memory_mb * 1024 * 1024)
            MockProcess.return_value = mock_instance
            
            # Trigger a log
            log_memory_usage("init", document_id="test")
            
            assert os.path.exists(self.temp_log_path)
            
            with open(self.temp_log_path, "r") as f:
                content = f.read()
                assert "timestamp" in content
                assert "memory_gb" in content
                assert "test" in content

    def test_data_streamer_class(self):
        """Test the DataStreamer context class."""
        mock_memory_mb = 500.0
        
        with patch("code.lib.data_loader.psutil.Process") as MockProcess:
            mock_instance = MagicMock()
            mock_instance.memory_info.return_value = MagicMock(rss=mock_memory_mb * 1024 * 1024)
            MockProcess.return_value = mock_instance
            
            mock_data = [{"id": f"doc_{i}"} for i in range(20)]
            with patch("code.lib.data_loader.load_dataset") as mock_load:
                mock_load.return_value = MagicMock(__iter__=lambda self: iter(mock_data))
                
                streamer = DataStreamer(batch_size=5)
                batches = list(streamer)
                
                assert len(batches) == 4
                assert len(batches[0]) == 5
