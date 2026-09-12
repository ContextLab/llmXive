"""
Unit tests for verify_data.py, specifically focusing on Geometry Calibration failures.
"""
import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure the code directory is in the path for imports
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from verify_data import (
    extract_geometry_metadata,
    main,
    load_json_file,
    load_yaml_file,
    find_bids_sidecars
)
from config import get_config

class TestGeometryCalibrationFailure:
    """
    Tests for the "Geometry Calibration" failure scenario as described in T071.
    Verifies that the system halts with the correct error message when
    required metadata is missing from the BIDS manifest.
    """

    def test_geometry_calibration_failure_missing_screen_width(self, caplog):
        """
        Asserts that the script halts with the correct error message when
        screen_width_px is missing from the metadata.
        """
        # Create a temporary directory structure mimicking a BIDS dataset
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_dir = Path(tmpdir)
            dataset_description = dataset_dir / "dataset_description.json"
            
            # Create a dataset_description.json with missing screen_width_px
            # but present viewing_distance_mm and sampling_rate_hz
            mock_data = {
                "Name": "Test Dataset",
                "BIDSVersion": "1.6.0",
                "viewing_distance_mm": 600,
                "sampling_rate_hz": 1000
            }
            
            with open(dataset_description, "w") as f:
                json.dump(mock_data, f)

            # Mock the load_json_file to return our mock data
            with patch('verify_data.load_json_file', return_value=mock_data):
                # Mock the verify_sources check to return False (strict mode)
                with patch('verify_data.load_verified_sources', return_value={'hypothetical': False}):
                    # Mock sys.exit to catch the halt
                    with patch('sys.exit') as mock_exit:
                        # Call the specific function or main logic that triggers the check
                        # Since extract_geometry_metadata is the core logic, we test it directly
                        # or simulate the main flow.
                        try:
                            # We need to simulate the flow in main or a wrapper that calls extract_geometry_metadata
                            # Let's call extract_geometry_metadata directly as it contains the logic
                            extract_geometry_metadata(dataset_dir)
                        except SystemExit as e:
                            # Expected behavior: sys.exit(1)
                            assert e.code == 1
                            assert mock_exit.called
                            # Verify the error message contains the specific text
                            # The message should be logged before exit
                            assert any("Cannot calibrate I-VT threshold without screen geometry" in record.message for record in caplog.records)
                            return

                        # If we reach here, the test failed because it didn't exit
                        pytest.fail("Expected SystemExit but none was raised")

    def test_geometry_calibration_failure_missing_viewing_distance(self, caplog):
        """
        Asserts that the script halts with the correct error message when
        viewing_distance_mm is missing.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_dir = Path(tmpdir)
            dataset_description = dataset_dir / "dataset_description.json"
            
            mock_data = {
                "Name": "Test Dataset",
                "BIDSVersion": "1.6.0",
                "screen_width_px": 1920,
                "sampling_rate_hz": 1000
            }
            
            with open(dataset_description, "w") as f:
                json.dump(mock_data, f)

            with patch('verify_data.load_json_file', return_value=mock_data):
                with patch('verify_data.load_verified_sources', return_value={'hypothetical': False}):
                    with patch('sys.exit') as mock_exit:
                        try:
                            extract_geometry_metadata(dataset_dir)
                        except SystemExit as e:
                            assert e.code == 1
                            assert any("Cannot calibrate I-VT threshold without screen geometry" in record.message for record in caplog.records)
                            return
                        
                        pytest.fail("Expected SystemExit but none was raised")

    def test_geometry_calibration_failure_missing_sampling_rate(self, caplog):
        """
        Asserts that the script halts with the correct error message when
        sampling_rate_hz is missing.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_dir = Path(tmpdir)
            dataset_description = dataset_dir / "dataset_description.json"
            
            mock_data = {
                "Name": "Test Dataset",
                "BIDSVersion": "1.6.0",
                "screen_width_px": 1920,
                "viewing_distance_mm": 600
            }
            
            with open(dataset_description, "w") as f:
                json.dump(mock_data, f)

            with patch('verify_data.load_json_file', return_value=mock_data):
                with patch('verify_data.load_verified_sources', return_value={'hypothetical': False}):
                    with patch('sys.exit') as mock_exit:
                        try:
                            extract_geometry_metadata(dataset_dir)
                        except SystemExit as e:
                            assert e.code == 1
                            assert any("Cannot calibrate I-VT threshold without screen geometry" in record.message for record in caplog.records)
                            return
                        
                        pytest.fail("Expected SystemExit but none was raised")

    def test_geometry_calibration_success(self, caplog):
        """
        Asserts that the script succeeds when all required metadata is present.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_dir = Path(tmpdir)
            dataset_description = dataset_dir / "dataset_description.json"
            
            mock_data = {
                "Name": "Test Dataset",
                "BIDSVersion": "1.6.0",
                "screen_width_px": 1920,
                "viewing_distance_mm": 600,
                "sampling_rate_hz": 1000
            }
            
            with open(dataset_description, "w") as f:
                json.dump(mock_data, f)

            with patch('verify_data.load_json_file', return_value=mock_data):
                with patch('verify_data.load_verified_sources', return_value={'hypothetical': False}):
                    with patch('sys.exit') as mock_exit:
                        try:
                            result = extract_geometry_metadata(dataset_dir)
                            # Should return a dict with the values
                            assert isinstance(result, dict)
                            assert result['screen_width_px'] == 1920
                            assert result['viewing_distance_mm'] == 600
                            assert result['sampling_rate_hz'] == 1000
                            mock_exit.assert_not_called()
                        except SystemExit:
                            pytest.fail("SystemExit raised unexpectedly on valid data")

    def test_geometry_calibration_hypothetical_mode_fallback(self, caplog):
        """
        Asserts that in hypothetical mode, missing metadata does NOT halt,
        but instead logs a warning and uses defaults.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_dir = Path(tmpdir)
            dataset_description = dataset_dir / "dataset_description.json"
            
            # Missing all geometry fields
            mock_data = {
                "Name": "Test Dataset",
                "BIDSVersion": "1.6.0"
            }
            
            with open(dataset_description, "w") as f:
                json.dump(mock_data, f)

            # Mock config to provide defaults
            mock_config = {
                'default_screen_width_px': 1920,
                'default_viewing_distance_mm': 600,
                'default_sampling_rate_hz': 1000
            }
            
            with patch('verify_data.load_json_file', return_value=mock_data):
                with patch('verify_data.load_verified_sources', return_value={'hypothetical': True}):
                    with patch('verify_data.get_config', return_value=mock_config):
                        with patch('sys.exit') as mock_exit:
                            try:
                                result = extract_geometry_metadata(dataset_dir)
                                # Should use defaults
                                assert result['screen_width_px'] == 1920
                                assert result['viewing_distance_mm'] == 600
                                assert result['sampling_rate_hz'] == 1000
                                # Should NOT exit
                                mock_exit.assert_not_called()
                                # Should log a warning
                                assert any("WARNING" in record.levelname for record in caplog.records)
                            except SystemExit:
                                pytest.fail("SystemExit raised in hypothetical mode")