"""
Unit tests for Calibration Logic and Validation.
Tests run_calibration, RMSE calculations, and threshold enforcement.
"""
import pytest
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from simulate.calibration import run_calibration


class TestCalibrationLogic:
    """Tests for the calibration logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.pilot_data_path = os.path.join(self.temp_dir, "pilot_data.csv")
        self.output_report_path = os.path.join(self.temp_dir, "calibration_report.json")
        self.bkt_params_path = os.path.join(self.temp_dir, "bkt_params.yaml")

        # Create mock pilot data
        self.mock_pilot_data = [
            {"student_id": 1, "problem_id": "p1", "correct": 1, "bkt_pred": 0.8},
            {"student_id": 2, "problem_id": "p2", "correct": 0, "bkt_pred": 0.2},
            {"student_id": 3, "problem_id": "p3", "correct": 1, "bkt_pred": 0.9},
            {"student_id": 4, "problem_id": "p4", "correct": 1, "bkt_pred": 0.7},
            {"student_id": 5, "problem_id": "p5", "correct": 0, "bkt_pred": 0.1},
            # ... simulate 50+ rows for real test, but here we test logic
        ]
        # Ensure >= 50 rows for the "missing data" test logic to pass the count check
        for i in range(6, 55):
            self.mock_pilot_data.append({
                "student_id": i, "problem_id": f"p{i}",
                "correct": 1 if i % 2 == 0 else 0,
                "bkt_pred": 0.5 if i % 2 == 0 else 0.4
            })

        # Write mock data
        with open(self.pilot_data_path, 'w') as f:
            f.write("student_id,problem_id,correct,bkt_pred\n")
            for row in self.mock_pilot_data:
                f.write(f"{row['student_id']},{row['problem_id']},{row['correct']},{row['bkt_pred']}\n")

    def teardown_method(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('simulate.calibration.load_pilot_data')
    def test_missing_data_raises(self, mock_load):
        """Test that missing pilot data raises an error."""
        mock_load.side_effect = FileNotFoundError("Pilot data not found")
        
        with pytest.raises(FileNotFoundError):
            run_calibration(
                pilot_data_path="nonexistent.csv",
                output_report_path=self.output_report_path,
                bkt_params_path=self.bkt_params_path
            )

    @patch('simulate.calibration.load_pilot_data')
    def test_insufficient_data_raises(self, mock_load):
        """Test that data with < 50 participants raises an error."""
        mock_load.return_value = [{"student_id": 1}]  # Only 1 record
        
        with pytest.raises(ValueError, match="Human pilot data.*missing.*< 50 records"):
            run_calibration(
                pilot_data_path=self.pilot_data_path,
                output_report_path=self.output_report_path,
                bkt_params_path=self.bkt_params_path
            )

    @patch('simulate.calibration.load_pilot_data')
    def test_rmse_calculation(self, mock_load):
        """Test that RMSE is calculated correctly."""
        # Mock data with known RMSE
        mock_data = [
            {"correct": 1, "bkt_pred": 0.9}, # diff 0.1
            {"correct": 0, "bkt_pred": 0.1}, # diff 0.1
            {"correct": 1, "bkt_pred": 0.6}, # diff 0.4
            {"correct": 1, "bkt_pred": 0.8}, # diff 0.2
        ]
        # Squared diffs: 0.01, 0.01, 0.16, 0.04 -> Sum = 0.22 -> Mean = 0.055 -> RMSE = sqrt(0.055) ~ 0.234
        mock_load.return_value = mock_data + [{"student_id": i, "correct": 0, "bkt_pred": 0.5} for i in range(5, 55)]

        # We expect this to fail the RMSE <= 0.15 check based on the mock data above
        # But we are testing that the function runs and calculates.
        # To test success, we need data with RMSE <= 0.15.
        # Let's create perfect data for a success test.
        
        perfect_data = [
            {"correct": 1, "bkt_pred": 1.0},
            {"correct": 0, "bkt_pred": 0.0},
        ] + [{"student_id": i, "correct": 0, "bkt_pred": 0.0} for i in range(3, 55)]
        
        mock_load.return_value = perfect_data

        result = run_calibration(
            pilot_data_path=self.pilot_data_path,
            output_report_path=self.output_report_path,
            bkt_params_path=self.bkt_params_path
        )
        
        assert result["calibration_valid"] is True
        assert result["rmse"] == 0.0
        assert os.path.exists(self.output_report_path)

    @patch('simulate.calibration.load_pilot_data')
    def test_threshold_failure(self, mock_load):
        """Test that calibration fails if RMSE > 0.15."""
        bad_data = [
            {"correct": 1, "bkt_pred": 0.0}, # diff 1.0
            {"correct": 0, "bkt_pred": 1.0}, # diff 1.0
        ] + [{"student_id": i, "correct": 0, "bkt_pred": 0.5} for i in range(3, 55)]
        
        mock_load.return_value = bad_data

        result = run_calibration(
            pilot_data_path=self.pilot_data_path,
            output_report_path=self.output_report_path,
            bkt_params_path=self.bkt_params_path
        )
        
        assert result["calibration_valid"] is False
        assert result["rmse"] > 0.15

    @patch('simulate.calibration.load_pilot_data')
    def test_updates_bkt_params_on_success(self, mock_load):
        """Test that bkt_params.yaml is updated on successful calibration."""
        perfect_data = [
            {"correct": 1, "bkt_pred": 1.0},
            {"correct": 0, "bkt_pred": 0.0},
        ] + [{"student_id": i, "correct": 0, "bkt_pred": 0.0} for i in range(3, 55)]
        
        mock_load.return_value = perfect_data

        run_calibration(
            pilot_data_path=self.pilot_data_path,
            output_report_path=self.output_report_path,
            bkt_params_path=self.bkt_params_path
        )

        assert os.path.exists(self.bkt_params_path)
        with open(self.bkt_params_path, 'r') as f:
            content = f.read()
            assert "calibration_status" in content
            assert "valid" in content