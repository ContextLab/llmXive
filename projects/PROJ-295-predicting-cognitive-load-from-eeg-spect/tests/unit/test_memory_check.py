import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
from code.data.memory_check import get_peak_memory_mb, run_memory_check


class TestMemoryCheck:
    """
    Unit tests for the memory_check module.
    """

    def test_get_peak_memory_mb_returns_positive(self):
        """Test that get_peak_memory_mb returns a positive number."""
        import tracemalloc
        tracemalloc.start()
        # Allocate some dummy memory
        _ = [0] * 10000
        mem = get_peak_memory_mb()
        tracemalloc.stop()
        assert mem >= 0.0

    @patch('code.data.memory_check.load_epochs_chunked')
    @patch('code.data.memory_check.estimate_memory_usage')
    @patch('code.data.memory_check.load_config')
    def test_run_memory_check_writes_report(
        self, 
        mock_load_config, 
        mock_estimate_usage, 
        mock_load_epochs
    ):
        """Test that run_memory_check writes a valid JSON report."""
        # Setup mocks
        mock_load_config.return_value = {}
        mock_estimate_usage.return_value = 100.0  # 100 MB estimate
        
        # Mock generator to yield one empty chunk
        def mock_generator():
            yield []
        
        mock_load_epochs.return_value = mock_generator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "report.json")
            
            result = run_memory_check(
                data_dir=tmpdir,
                output_path=output_path,
                chunk_size=5,
                max_memory_gb=6.5
            )

            # Verify return value
            assert isinstance(result, dict)
            assert "status" in result
            assert "peak_memory_mb" in result
            assert "peak_memory_gb" in result
            assert "timestamp" in result

            # Verify file was written
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                written_data = json.load(f)
            
            assert written_data["status"] == "passed" # Should pass with low mock usage
            assert written_data["chunks_processed"] == 1

    @patch('code.data.memory_check.load_epochs_chunked')
    @patch('code.data.memory_check.estimate_memory_usage')
    @patch('code.data.memory_check.load_config')
    def test_run_memory_check_fails_on_high_memory(
        self,
        mock_load_config,
        mock_estimate_usage,
        mock_load_epochs
    ):
        """Test that status is 'failed' if memory exceeds limit."""
        mock_load_config.return_value = {}
        mock_estimate_usage.return_value = 100.0

        def mock_generator():
            yield []

        mock_load_epochs.return_value = mock_generator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "report.json")
            
            # Set a very low limit (0.001 GB = 1 MB) to force failure
            result = run_memory_check(
                data_dir=tmpdir,
                output_path=output_path,
                chunk_size=5,
                max_memory_gb=0.001
            )

            assert result["status"] == "failed"
            assert "failed" in result["message"]
            
            with open(output_path, 'r') as f:
                written_data = json.load(f)
            
            assert written_data["status"] == "failed"

    @patch('code.data.memory_check.load_epochs_chunked')
    @patch('code.data.memory_check.estimate_memory_usage')
    @patch('code.data.memory_check.load_config')
    def test_run_memory_check_handles_exception(
        self,
        mock_load_config,
        mock_estimate_usage,
        mock_load_epochs
    ):
        """Test that the function handles exceptions gracefully."""
        mock_load_config.return_value = {}
        mock_estimate_usage.return_value = 100.0
        
        # Force an exception in the loader
        mock_load_epochs.side_effect = RuntimeError("Simulated load error")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "report.json")
            
            result = run_memory_check(
                data_dir=tmpdir,
                output_path=output_path,
                chunk_size=5,
                max_memory_gb=6.5
            )

            assert result["status"] == "error"
            assert "Simulated load error" in result["message"]
            
            with open(output_path, 'r') as f:
                written_data = json.load(f)
            
            assert written_data["status"] == "error"