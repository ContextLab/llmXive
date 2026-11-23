"""
Unit tests for TDP Constant Generation Script (T008c).
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
# We need to adjust the import path to match the project structure
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from code.utils.generate_tdp_constant import (
    load_calibration_data,
    calculate_error_margin_and_ci,
    generate_calibrated_tdp,
    CalibrationDataError,
    PROJECT_ROOT,
    CALIBRATION_INPUT_PATH,
    OUTPUT_PATH
)


class TestLoadCalibrationData:
    """Tests for load_calibration_data function."""

    def test_file_not_found_raises_error(self, tmp_path):
        """Should raise CalibrationDataError if file doesn't exist."""
        fake_path = tmp_path / "nonexistent.json"
        with pytest.raises(CalibrationDataError) as exc_info:
            load_calibration_data(fake_path)
        assert "not found" in str(exc_info.value)

    def test_invalid_json_raises_error(self, tmp_path):
        """Should raise CalibrationDataError for malformed JSON."""
        fake_path = tmp_path / "calibration.json"
        fake_path.write_text("{ invalid json }")
        with pytest.raises(CalibrationDataError) as exc_info:
            load_calibration_data(fake_path)
        assert "Invalid JSON" in str(exc_info.value)

    def test_missing_required_fields_raises_error(self, tmp_path):
        """Should raise CalibrationDataError if required fields are missing."""
        fake_path = tmp_path / "calibration.json"
        fake_path.write_text(json.dumps({"workload_type": "test"}))  # Missing others
        with pytest.raises(CalibrationDataError) as exc_info:
            load_calibration_data(fake_path)
        assert "missing required fields" in str(exc_info.value).lower()

    def test_negative_tdp_raises_error(self, tmp_path):
        """Should raise CalibrationDataError for non-positive TDP."""
        fake_path = tmp_path / "calibration.json"
        fake_path.write_text(json.dumps({
            "workload_type": "test",
            "cpu_percent": 80.0,
            "duration": 10.0,
            "estimated_tdp_watts": -50.0
        }))
        with pytest.raises(CalibrationDataError) as exc_info:
            load_calibration_data(fake_path)
        assert "must be positive" in str(exc_info.value)

    def test_failed_status_raises_error(self, tmp_path):
        """Should raise CalibrationDataError if status indicates failure."""
        fake_path = tmp_path / "calibration.json"
        fake_path.write_text(json.dumps({
            "workload_type": "test",
            "cpu_percent": 80.0,
            "duration": 10.0,
            "estimated_tdp_watts": 65.0,
            "status": "failed"
        }))
        with pytest.raises(CalibrationDataError) as exc_info:
            load_calibration_data(fake_path)
        assert "reported failure" in str(exc_info.value)

    def test_successfully_loads_valid_data(self, tmp_path):
        """Should return data dict for valid input."""
        fake_path = tmp_path / "calibration.json"
        expected_data = {
            "workload_type": "matrix_multiply",
            "cpu_percent": 85.5,
            "duration": 15.2,
            "estimated_tdp_watts": 65.0
        }
        fake_path.write_text(json.dumps(expected_data))

        result = load_calibration_data(fake_path)
        assert result == expected_data


class TestCalculateErrorMarginAndCi:
    """Tests for error margin and confidence interval calculation."""

    def test_calculates_positive_values(self):
        """Should return positive error margin and CI width."""
        error, ci = calculate_error_margin_and_ci(65.0, 80.0, 10.0)
        assert error > 0
        assert ci > 0

    def test_error_scales_with_cpu_utilization(self):
        """Error margin should be larger for lower CPU utilization."""
        error_high_cpu, _ = calculate_error_margin_and_ci(65.0, 95.0, 10.0)
        error_low_cpu, _ = calculate_error_margin_and_ci(65.0, 50.0, 10.0)
        assert error_low_cpu > error_high_cpu

    def test_error_scales_with_tdp(self):
        """Error margin should scale linearly with TDP."""
        error_65, _ = calculate_error_margin_and_ci(65.0, 80.0, 10.0)
        error_130, _ = calculate_error_margin_and_ci(130.0, 80.0, 10.0)
        # Should be approximately double
        assert abs(error_130 - 2 * error_65) < 0.01 * error_65


class TestGenerateCalibratedTdp:
    """Tests for generate_calibrated_tdp function."""

    def test_produces_required_fields(self):
        """Output must contain tdp_watts, source, error_margin, confidence_interval."""
        calibration_data = {
            "workload_type": "test",
            "cpu_percent": 80.0,
            "duration": 10.0,
            "estimated_tdp_watts": 65.0
        }
        result = generate_calibrated_tdp(calibration_data)

        assert "tdp_watts" in result
        assert "source" in result
        assert "error_margin" in result
        assert "confidence_interval" in result

    def test_source_is_calibration(self):
        """Source field must be 'calibration'."""
        calibration_data = {
            "workload_type": "test",
            "cpu_percent": 80.0,
            "duration": 10.0,
            "estimated_tdp_watts": 65.0
        }
        result = generate_calibrated_tdp(calibration_data)
        assert result["source"] == "calibration"

    def test_includes_calibration_source_metadata(self):
        """Output should include calibration source details."""
        calibration_data = {
            "workload_type": "matrix_multiply",
            "cpu_percent": 85.0,
            "duration": 12.5,
            "estimated_tdp_watts": 70.0
        }
        result = generate_calibrated_tdp(calibration_data)

        assert "calibration_source" in result
        assert result["calibration_source"]["workload_type"] == "matrix_multiply"
        assert result["calibration_source"]["cpu_percent"] == 85.0
        assert result["calibration_source"]["duration_seconds"] == 12.5


class TestIntegration:
    """Integration tests simulating the full script execution."""

    def test_full_flow_with_valid_data(self, tmp_path):
        """Test complete flow from calibration data to output file."""
        # Setup temporary paths
        input_path = tmp_path / "calibration_run.json"
        output_path = tmp_path / "calibrated_tdp.json"

        # Create valid calibration data
        calibration_data = {
            "workload_type": "matrix_multiply",
            "cpu_percent": 90.0,
            "duration": 20.0,
            "estimated_tdp_watts": 80.0
        }
        input_path.write_text(json.dumps(calibration_data))

        # Mock the module's path constants
        with patch(
            'code.utils.generate_tdp_constant.CALIBRATION_INPUT_PATH',
            input_path
        ), patch(
            'code.utils.generate_tdp_constant.OUTPUT_PATH',
            output_path
        ):
            # Re-import to pick up mocked paths (or call functions directly)
            from code.utils.generate_tdp_constant import (
                load_calibration_data,
                generate_calibrated_tdp,
                save_calibrated_tdp
            )

            data = load_calibration_data(input_path)
            result = generate_calibrated_tdp(data)
            save_calibrated_tdp(result, output_path)

        # Verify output file exists and contains correct structure
        assert output_path.exists()
        output_data = json.loads(output_path.read_text())

        assert output_data["tdp_watts"] == 80.0
        assert output_data["source"] == "calibration"
        assert "error_margin" in output_data
        assert "confidence_interval" in output_data

    def test_fails_loudly_on_missing_calibration(self, tmp_path, capsys):
        """Script should fail if calibration file is missing."""
        output_path = tmp_path / "calibrated_tdp.json"

        with patch(
            'code.utils.generate_tdp_constant.CALIBRATION_INPUT_PATH',
            tmp_path / "nonexistent.json"
        ), patch(
            'code.utils.generate_tdp_constant.OUTPUT_PATH',
            output_path
        ):
            from code.utils.generate_tdp_constant import main
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower()