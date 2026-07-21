"""
Unit tests for T032: Additional unit tests for edge cases (n < 300 warning logic).

This module tests the validator logic in code/validator.py, specifically
the mandatory fallback behavior when sample count is less than 300.
"""

import os
import json
import logging
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Adjust import path to match project structure
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from validator import check_sample_count, run_validation

# Configure logging for test visibility
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class TestSampleCountEdgeCases:
    """Test cases for n < 300 warning and fallback logic."""

    def test_sample_count_above_threshold_no_warning(self, caplog):
        """Test that n >= 300 does not trigger a warning."""
        with caplog.at_level(logging.WARNING):
            result = check_sample_count(n=300, threshold=300)
            assert result == {"status": "pass", "n": 300, "threshold": 300}
            assert "WARNING" not in caplog.text
            assert "fallback" not in caplog.text.lower()

    def test_sample_count_just_below_threshold_triggers_warning(self, caplog):
        """Test that n = 299 triggers a warning and fallback logic."""
        with caplog.at_level(logging.WARNING):
            result = check_sample_count(n=299, threshold=300)
            assert result == {"status": "fallback_required", "n": 299, "threshold": 300}
            assert "WARNING" in caplog.text
            assert "n < 300" in caplog.text
            assert "fallback" in caplog.text.lower()

    def test_sample_count_zero_triggers_warning(self, caplog):
        """Test that n = 0 triggers a warning and fallback logic."""
        with caplog.at_level(logging.WARNING):
            result = check_sample_count(n=0, threshold=300)
            assert result == {"status": "fallback_required", "n": 0, "threshold": 300}
            assert "WARNING" in caplog.text
            assert "n < 300" in caplog.text

    def test_sample_count_negative_triggers_warning(self, caplog):
        """Test that negative n triggers a warning."""
        with caplog.at_level(logging.WARNING):
            result = check_sample_count(n=-5, threshold=300)
            assert result == {"status": "fallback_required", "n": -5, "threshold": 300}
            assert "WARNING" in caplog.text
            assert "n < 300" in caplog.text

    def test_fallback_logic_generates_k2_labels(self, tmp_path):
        """Test that the fallback logic generates the required k=2 labels file."""
        # Create a temporary output directory
        output_dir = tmp_path / "processed"
        output_dir.mkdir()
        fallback_path = output_dir / "fallback_k2_labels.csv"

        # Mock the file writing to ensure it happens
        with patch("pandas.DataFrame.to_csv") as mock_to_csv:
            result = check_sample_count(n=100, threshold=300, output_path=str(fallback_path))
            
            assert result["status"] == "fallback_required"
            # Verify to_csv was called to create the fallback file
            mock_to_csv.assert_called_once()
            # Verify the path used matches the expected output
            call_args = mock_to_csv.call_args
            assert call_args[0][0] == str(fallback_path)

    def test_run_validation_with_low_sample_count(self, tmp_path):
        """Test that run_validation handles low sample count correctly."""
        # Create a dummy input file
        input_file = tmp_path / "ablation_labels_train.json"
        input_file.write_text(json.dumps([{"layer_id": 1, "utility_score": 0.5}]))
        
        output_dir = tmp_path / "processed"
        output_dir.mkdir()
        fallback_path = output_dir / "fallback_k2_labels.csv"

        with patch("pandas.DataFrame.to_csv") as mock_to_csv:
            result = run_validation(
                input_path=str(input_file),
                output_dir=str(output_dir),
                threshold=300
            )
            
            assert result["status"] == "fallback_required"
            mock_to_csv.assert_called_once()
            assert "fallback_k2_labels.csv" in str(mock_to_csv.call_args[0][0])

    def test_run_validation_with_high_sample_count(self, tmp_path):
        """Test that run_validation proceeds normally with sufficient samples."""
        # Create a dummy input file with enough samples (mocked via patch)
        input_file = tmp_path / "ablation_labels_train.json"
        # Create a list of 301 items to simulate sufficient data
        data = [{"layer_id": i, "utility_score": 0.5} for i in range(301)]
        input_file.write_text(json.dumps(data))
        
        output_dir = tmp_path / "processed"
        output_dir.mkdir()
        
        # Mock the file writing to avoid actual disk I/O for this test
        with patch("pandas.DataFrame.to_csv") as mock_to_csv:
            result = run_validation(
                input_path=str(input_file),
                output_dir=str(output_dir),
                threshold=300
            )
            
            assert result["status"] == "pass"
            # In a real scenario, this would process the data, but we're just checking flow
            # The mock ensures we don't actually write files during unit tests

    def test_threshold_parameter_variations(self, caplog):
        """Test that the threshold parameter can be adjusted."""
        with caplog.at_level(logging.WARNING):
            # Test with threshold = 100
            result = check_sample_count(n=99, threshold=100)
            assert result["status"] == "fallback_required"
            assert "n < 100" in caplog.text

if __name__ == "__main__":
    pytest.main([__file__, "-v"])