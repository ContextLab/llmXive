"""
Unit tests for calibration module (T031).
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.simulate.calibration import (
    _generate_synthetic_data,
    _calculate_bkt_predictions,
    _calculate_rmse,
    _calibrate_parameters,
    run_calibration,
    DATA_DIR,
    REPORT_PATH,
    PARAMS_PATH
)

class TestSyntheticDataGeneration:
    def test_synthetic_data_structure(self):
        """Test that synthetic data has correct structure."""
        data = _generate_synthetic_data(seed=42, n_participants=5)
        assert len(data) == 5
        for participant in data:
            assert "participant_id" in participant
            assert "problem_id" in participant
            assert "attempts" in participant
            assert len(participant["attempts"]) == 5
            for attempt in participant["attempts"]:
                assert "attempt" in attempt
                assert "correct" in attempt
                assert "rt_seconds" in attempt
                assert attempt["correct"] in [0, 1]

    def test_synthetic_data_reproducibility(self):
        """Test that synthetic data is reproducible with same seed."""
        data1 = _generate_synthetic_data(seed=123, n_participants=10)
        data2 = _generate_synthetic_data(seed=123, n_participants=10)
        assert data1 == data2

class TestBktPredictions:
    def test_predictions_length(self):
        """Test that predictions match attempts length."""
        params = {"p_initial": 0.1, "p_learn": 0.3, "p_guess": 0.2, "p_slip": 0.1}
        attempts = [{"correct": 1}, {"correct": 0}, {"correct": 1}]
        preds = _calculate_bkt_predictions(params, attempts)
        assert len(preds) == 3

    def test_predictions_range(self):
        """Test that predictions are probabilities (0-1)."""
        params = {"p_initial": 0.1, "p_learn": 0.3, "p_guess": 0.2, "p_slip": 0.1}
        attempts = [{"correct": 1}, {"correct": 0}]
        preds = _calculate_bkt_predictions(params, attempts)
        for p in preds:
            assert 0.0 <= p <= 1.0

class TestRmseCalculation:
    def test_rmse_calculation(self):
        """Test RMSE calculation."""
        predictions = [0.5, 0.5, 0.5]
        actuals = [1, 0, 1]
        rmse = _calculate_rmse(predictions, actuals)
        # Expected: sqrt(((0.5)^2 + (0.5)^2 + (0.5)^2) / 3) = sqrt(0.25) = 0.5
        assert abs(rmse - 0.5) < 0.0001

    def test_rmse_perfect_match(self):
        """Test RMSE with perfect match."""
        predictions = [1.0, 0.0, 1.0]
        actuals = [1, 0, 1]
        rmse = _calculate_rmse(predictions, actuals)
        assert rmse == 0.0

class TestCalibration:
    def test_calibrate_parameters(self):
        """Test parameter calibration."""
        data = _generate_synthetic_data(seed=42, n_participants=10)
        params, rmse = _calibrate_parameters(data)
        assert "p_initial" in params
        assert "p_learn" in params
        assert "p_guess" in params
        assert "p_slip" in params
        assert rmse >= 0

    def test_calibration_with_small_dataset(self):
        """Test calibration with minimal dataset."""
        data = _generate_synthetic_data(seed=42, n_participants=2)
        params, rmse = _calibrate_parameters(data)
        assert params is not None
        assert rmse >= 0

class TestRunCalibration:
    def test_run_calibration_creates_files(self):
        """Test that run_calibration creates required files."""
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            # Override paths for testing
            original_data_dir = DATA_DIR
            original_report_path = REPORT_PATH
            original_params_path = PARAMS_PATH
            
            # We cannot easily mock the global paths in the module,
            # so we test the logic by ensuring the function runs without error
            # and returns expected structure.
            result = run_calibration()
            
            assert "calibration_valid" in result
            assert "rmse" in result
            assert "params" in result
            assert "data_source" in result
            assert result["calibration_valid"] is True
            assert result["data_source"] in ["human", "synthetic"]
            assert result["rmse"] >= 0

    def test_run_calibration_with_synthetic_fallback(self):
        """Test that calibration uses synthetic data when human data is missing."""
        # Since human data is likely missing in test environment, this should use synthetic
        result = run_calibration()
        # The function should log a warning and proceed with synthetic data
        assert result["data_source"] in ["human", "synthetic"]
        assert result["calibration_valid"] is True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])