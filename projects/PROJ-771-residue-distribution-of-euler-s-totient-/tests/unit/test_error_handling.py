import pytest
import os
import sys
import logging
from unittest.mock import patch, MagicMock
import json
import tempfile
import shutil

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from sieve import compute_phi_linear_sieve, log_error, run_sieve_analysis, ResidueDataset, save_residue_dataset, MemoryGuard

# Setup logging to capture output
logging.basicConfig(level=logging.DEBUG)

class TestErrorHandling:
    """Tests for T014: Error handling to log specific n if sieve fails."""

    def test_log_error_captures_n(self, caplog):
        """Verify that log_error includes the specific n in the message."""
        with caplog.at_level(logging.ERROR):
            log_error("Test failure", n=12345)
        
        assert "n=12345" in caplog.text
        assert "Test failure" in caplog.text

    def test_log_error_no_n(self, caplog):
        """Verify that log_error works without n."""
        with caplog.at_level(logging.ERROR):
            log_error("General failure")
        
        assert "n=" not in caplog.text
        assert "General failure" in caplog.text

    @patch('sieve.MemoryGuard')
    def test_sieve_memory_failure_logs_error(self, MockGuard, caplog):
        """
        Verify that if MemoryGuard.check() returns False (memory limit reached),
        the error is logged and the function returns None/error, NOT saving data.
        """
        # Mock the guard to fail immediately
        mock_guard_instance = MagicMock()
        mock_guard_instance.check.return_value = False
        MockGuard.return_value = mock_guard_instance

        # Run sieve with a small N to trigger the mock
        with caplog.at_level(logging.ERROR):
            phi, error = compute_phi_linear_sieve(100)
        
        assert error is not None
        assert "Memory limit" in error
        assert phi is None
        # Verify log was called
        assert any("Memory limit" in record.message for record in caplog.records)

    def test_run_sieve_does_not_save_on_error(self, tmp_path):
        """
        Verify that run_sieve_analysis does not attempt to save if an error occurs.
        We simulate an error by mocking compute_phi_linear_sieve to return an error.
        """
        output_dir = str(tmp_path)
        
        # Mock compute_phi_linear_sieve to simulate failure
        with patch('sieve.compute_phi_linear_sieve') as mock_compute:
            mock_compute.return_value = (None, "Simulated sieve failure at n=999999")
            
            # Run analysis
            results = run_sieve_analysis(1000, [3], output_dir)
            
            # Check result
            assert results[3]['status'] == 'failed'
            
            # Verify no file was created
            expected_file = os.path.join(output_dir, "residues_3_1000.json")
            assert not os.path.exists(expected_file), "File should not be created if sieve fails"

    def test_memory_guard_trigger(self):
        """Test that MemoryGuard correctly identifies high memory usage."""
        # This is a unit test for the guard logic itself
        # We can't easily trigger real OOM, but we can test the logic
        guard = MemoryGuard(limit_mb=10, check_interval=1)
        
        # Mock process memory info
        with patch.object(guard, 'process') as mock_process:
            # Simulate 95% usage
            mock_process.memory_info.return_value.rss = int(10 * 1024 * 1024 * 0.95)
            
            result = guard.check()
            assert result is False, "Should return False when usage >= 90%"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])