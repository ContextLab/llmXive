import pytest
import os
import sys
import hashlib
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from reproducibility_check import run_pipeline_with_seed, compare_runs

class TestReproducibility:
    """Unit tests for reproducibility checking functionality."""

    def test_run_pipeline_with_seed_success(self):
        """Test that run_pipeline_with_seed returns success and hashes when pipeline runs."""
        # Mock the subprocess.run to simulate a successful pipeline run
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        
        with patch('reproducibility_check.subprocess.run', return_value=mock_result):
            with patch('reproducibility_check.Path.exists', return_value=True):
                with patch('builtins.open', mock_open_with_data(b"test content")):
                    result = run_pipeline_with_seed(42, "test_output")
                    
                    assert result["success"] is True
                    assert "hashes" in result
                    assert all(v is not None for v in result["hashes"].values())

    def test_run_pipeline_with_seed_failure(self):
        """Test that run_pipeline_with_seed handles pipeline failures correctly."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Pipeline failed"
        
        with patch('reproducibility_check.subprocess.run', return_value=mock_result):
            result = run_pipeline_with_seed(42, "test_output")
            
            assert result["success"] is False
            assert "error" in result
            assert "Pipeline failed" in result["error"]

    def test_compare_runs_success(self):
        """Test that compare_runs correctly identifies matching runs."""
        run1 = {
            "success": True,
            "hashes": {
                "imputed_data_hash": "abc123",
                "regression_coefficients_hash": "def456"
            }
        }
        
        run2 = {
            "success": True,
            "hashes": {
                "imputed_data_hash": "abc123",
                "regression_coefficients_hash": "def456"
            }
        }
        
        comparison = compare_runs(run1, run2)
        
        assert comparison["reproducible"] is True
        assert comparison["summary"].startswith("Reproducibility check: PASSED")

    def test_compare_runs_failure(self):
        """Test that compare_runs correctly identifies non-matching runs."""
        run1 = {
            "success": True,
            "hashes": {
                "imputed_data_hash": "abc123",
                "regression_coefficients_hash": "def456"
            }
        }
        
        run2 = {
            "success": True,
            "hashes": {
                "imputed_data_hash": "xyz789",  # Different hash
                "regression_coefficients_hash": "def456"
            }
        }
        
        comparison = compare_runs(run1, run2)
        
        assert comparison["reproducible"] is False
        assert "Hash mismatch detected" in comparison["summary"]
        assert len(comparison["differences"]) > 0

    def test_compare_runs_failure_scenario(self):
        """Test comparison when one or both runs failed."""
        run1 = {"success": False, "error": "Failed to run pipeline"}
        run2 = {"success": True, "hashes": {"imputed_data_hash": "abc123"}}
        
        comparison = compare_runs(run1, run2)
        
        assert comparison["reproducible"] is False
        assert "One or both runs failed" in comparison["reason"]

def mock_open_with_data(data):
    """Helper function to mock open() with specific data."""
    from unittest.mock import mock_open
    m = mock_open(read_data=data.decode() if isinstance(data, bytes) else data)
    return m