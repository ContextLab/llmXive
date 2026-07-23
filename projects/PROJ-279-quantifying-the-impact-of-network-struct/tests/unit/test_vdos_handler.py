"""
Unit tests for VDOS Handling (Task T024).
"""
import json
import os
import tempfile
from pathlib import Path
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

# Mock the environment config to avoid dependency on actual .env files during unit tests
import sys
from unittest.mock import MagicMock

# Mock the config module
mock_config = MagicMock()
mock_config.get_processed_dir.return_value = Path("/tmp/test_project/data/processed")
mock_config.get_logger = lambda name: MagicMock()

# Inject mocks before importing the module
sys.modules['config'] = MagicMock()
sys.modules['config.env_config'] = mock_config
sys.modules['validation_utils'] = MagicMock()

from vdos_handler import load_vdos, calculate_participation_ratios, process_configs_with_vdos, save_vdos_missing_report

class TestVDOSHandler:
    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.vdos_dir = Path(self.temp_dir) / "vdos"
        self.vdos_dir.mkdir(parents=True, exist_ok=True)

    def test_load_vdos_success(self):
        """Test loading VDOS when file exists."""
        config_id = "test_config_001"
        file_path = self.vdos_dir / f"{config_id}.npy"
        
        # Create a dummy VDOS array
        dummy_vdos = np.array([1.0, 2.0, 3.0, 4.0])
        np.save(file_path, dummy_vdos)
        
        # Mock the get_processed_dir to point to our temp dir's parent
        with patch('vdos_handler.get_processed_dir', return_value=Path(self.temp_dir)):
            result = load_vdos(config_id, raw_dir=Path(self.temp_dir))
            
        assert result is not None
        np.testing.assert_array_equal(result, dummy_vdos)

    def test_load_vdos_missing(self, caplog):
        """Test loading VDOS when file is missing."""
        config_id = "missing_config"
        
        with patch('vdos_handler.get_processed_dir', return_value=Path(self.temp_dir)):
            result = load_vdos(config_id, raw_dir=Path(self.temp_dir))
            
        assert result is None
        # Verify error was logged (check caplog if configured, or just assert None)
        # The function logs via logger, which is mocked in the import but we can check logic
        # Since we mocked get_logger, we can't easily check logs, but we assert None.

    def test_calculate_participation_ratios_1d(self):
        """Test PR calculation on 1D array (assuming it's PR spectrum)."""
        vdos = np.array([0.1, 0.2, 0.3, 0.4])
        pr = calculate_participation_ratios(vdos, None)
        
        # If input is PR per mode, mean is expected
        expected_mean = np.mean(vdos)
        assert np.isclose(pr, expected_mean)

    def test_calculate_participation_ratios_zero_sum(self):
        """Test PR calculation with zero sum."""
        vdos = np.array([0.0, 0.0, 0.0])
        pr = calculate_participation_ratios(vdos, None)
        assert pr == 0.0

    def test_process_configs_with_vdos(self):
        """Test processing multiple configs."""
        # Setup files
        config_ids = ["cfg_1", "cfg_2", "cfg_3"]
        for cid in config_ids:
            path = self.vdos_dir / f"{cid}.npy"
            np.save(path, np.array([1.0, 1.0]))
        
        # Remove one to simulate missing
        missing_path = self.vdos_dir / "cfg_2.npy"
        os.remove(missing_path)
        
        with patch('vdos_handler.get_processed_dir', return_value=Path(self.temp_dir)):
            successful, excluded = process_configs_with_vdos(config_ids, raw_dir=Path(self.temp_dir))
        
        assert "cfg_1" in successful
        assert "cfg_3" in successful
        assert len(excluded) == 1
        assert excluded[0]["config_id"] == "cfg_2"
        assert "ERR-VDOS-MISSING" in excluded[0]["reason"]

    def test_save_vdos_missing_report(self):
        """Test saving the missing report."""
        excluded = [
            {"config_id": "bad_1", "reason": "Missing"},
            {"config_id": "bad_2", "reason": "Invalid"}
        ]
        output_path = Path(self.temp_dir) / "vdos_missing_report.json"
        
        save_vdos_missing_report(excluded, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        assert report["count"] == 2
        assert report["excluded_configs"] == excluded