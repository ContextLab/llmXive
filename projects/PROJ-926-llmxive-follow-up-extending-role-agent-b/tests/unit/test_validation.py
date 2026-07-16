"""
Unit tests for src/sim/validation.py
"""
import json
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from src.sim.validation import (
    compute_checksum,
    save_raw_ground_truth_logs,
    validate_trajectory
)


class TestValidation:
    """Test suite for validation utilities."""

    def test_compute_checksum(self):
        """Test checksum computation for a file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            checksum = compute_checksum(temp_path)
            assert len(checksum) == 64  # SHA256 hex length
            assert isinstance(checksum, str)
        finally:
            os.unlink(temp_path)

    def test_save_raw_ground_truth_logs_creates_file(self):
        """Test that save_raw_ground_truth_logs creates the output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_gt.json")
            
            # Mock the run_episode function to avoid needing ALFWorld
            with patch('src.sim.validation.run_episode') as mock_run:
                mock_run.return_value = {
                    "state_transitions": [{"step": 1, "state": "test"}],
                    "action_log": [{"action": "test"}],
                    "success": True
                }
                
                result = save_raw_ground_truth_logs(output_path, force_generate=True)
                
                assert os.path.exists(output_path)
                assert result["record_count"] == 10  # We generate 10 episodes
                assert "checksum" in result
                
                # Verify file content
                with open(output_path, 'r') as f:
                    data = json.load(f)
                    assert len(data) == 10
                    assert data[0]["source"] == "simulated_ground_truth"

    def test_validate_trajectory_empty_logs(self):
        """Test validation with empty logs."""
        result = validate_trajectory([], [])
        assert result["valid"] is False
        assert "Empty" in result["reason"]

    def test_validate_trajectory_mismatched_lengths(self):
        """Test validation with mismatched log lengths."""
        action_log = [{"action": "1"}]
        ground_truth_log = [{"state": "1"}, {"state": "2"}]
        
        result = validate_trajectory(action_log, ground_truth_log)
        assert result["valid"] is False
        assert "mismatch" in result["reason"]

    def test_validate_trajectory_success(self):
        """Test validation with matching logs."""
        action_log = [{"action": "1"}, {"action": "2"}]
        ground_truth_log = [{"state": "1"}, {"state": "2"}]
        
        result = validate_trajectory(action_log, ground_truth_log)
        assert result["valid"] is True