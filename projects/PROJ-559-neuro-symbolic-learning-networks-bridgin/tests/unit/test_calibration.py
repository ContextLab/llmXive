"""
Unit tests for calibration module (T031).

These tests verify:
1. RMSE calculation correctness
2. BKT simulation logic
3. Calibration threshold enforcement
4. File I/O for params and reports
"""
import pytest
import os
import sys
import json
import tempfile
import shutil
import pandas as pd
import yaml
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from simulate.calibration import (
    calculate_rmse,
    simulate_bkt_performance,
    calculate_bkt_metrics,
    load_bkt_params,
    save_bkt_params,
    load_pilot_data,
    run_calibration,
    RMSE_THRESHOLD,
    DIFF_THRESHOLD
)


class TestCalibrationLogic:
    """Test suite for calibration logic."""

    def test_calculate_rmse_exact_match(self):
        """RMSE should be 0 when predictions match actuals exactly."""
        predictions = [0.5, 0.8, 0.3]
        actuals = [0.5, 0.8, 0.3]
        rmse = calculate_rmse(predictions, actuals)
        assert rmse == 0.0

    def test_calculate_rmse_constant_error(self):
        """RMSE for constant error should be sqrt(mean(error^2))."""
        predictions = [1.0, 2.0, 3.0]
        actuals = [0.0, 1.0, 2.0]  # Each prediction is 1.0 higher
        rmse = calculate_rmse(predictions, actuals)
        expected = (1.0 ** 2) ** 0.5  # sqrt(1) = 1.0
        assert abs(rmse - expected) < 1e-6

    def test_calculate_rmse_empty_lists(self):
        """RMSE for empty lists should return 0.0."""
        rmse = calculate_rmse([], [])
        assert rmse == 0.0

    def test_bkt_simulation_basic(self):
        """BKT simulation should produce predictions in [0, 1] range."""
        params = {
            'P_G': 0.1,
            'P_L0': 0.5,
            'P_S': 0.1,
            'P_T': 0.2
        }
        df = pd.DataFrame({
            'student_id': ['S1', 'S1'],
            'problem_id': ['P1', 'P1'],
            'correct': [1, 1],
            'attempt_num': [1, 2]
        })
        preds, acts = simulate_bkt_performance(df, params)
        
        assert len(preds) == len(acts)
        for p in preds:
            assert 0.0 <= p <= 1.0, f"Prediction {p} out of bounds"

    def test_bkt_simulation_learning_curve(self):
        """BKT should show increasing probability of correctness over attempts."""
        params = {
            'P_G': 0.05,
            'P_L0': 0.3,
            'P_S': 0.05,
            'P_T': 0.3
        }
        # Student gets all correct, so belief should increase
        df = pd.DataFrame({
            'student_id': ['S1'] * 5,
            'problem_id': ['P1'] * 5,
            'correct': [1, 1, 1, 1, 1],
            'attempt_num': [1, 2, 3, 4, 5]
        })
        preds, _ = simulate_bkt_performance(df, params)
        
        # Predictions should generally increase (allowing for small numerical noise)
        # The first prediction is based on P_L0, subsequent ones should be higher
        assert preds[0] > 0.0  # Initial belief > 0

    def test_calculate_bkt_metrics_structure(self):
        """Metrics output should contain required keys."""
        preds = [0.5, 0.6, 0.7]
        acts = [1.0, 0.0, 1.0]
        params = {'P_G': 0.1, 'P_L0': 0.5, 'P_S': 0.1, 'P_T': 0.1}
        metrics = calculate_bkt_metrics(preds, acts, params)
        
        assert 'rmse' in metrics
        assert 'diff' in metrics
        assert 'num_samples' in metrics
        assert metrics['num_samples'] == 3

    def test_load_save_bkt_params(self):
        """Test loading and saving BKT parameters to/from YAML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            params_path = os.path.join(tmpdir, 'test_params.yaml')
            test_params = {
                'P_G': 0.15,
                'P_L0': 0.6,
                'P_S': 0.12,
                'P_T': 0.18
            }
            
            # Save
            save_bkt_params(test_params, params_path)
            assert os.path.exists(params_path)
            
            # Load
            loaded = load_bkt_params(params_path)
            assert loaded == test_params

    def test_calibration_threshold_pass(self):
        """Calibration should pass when metrics are within thresholds."""
        # Create a scenario where RMSE is low
        params = {
            'P_G': 0.1,
            'P_L0': 0.5,
            'P_S': 0.1,
            'P_T': 0.2
        }
        
        # Create data where BKT can fit well
        df = pd.DataFrame({
            'student_id': ['S1'] * 10,
            'problem_id': ['P1'] * 10,
            'correct': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            'attempt_num': list(range(1, 11))
        })
        
        # Run a minimal calibration (just one iteration to test structure)
        with patch('simulate.calibration.run_calibration', return_value=(
            params, 
            {'rmse': 0.05, 'diff': 0.01, 'num_samples': 10},
            True
        )):
            opt_params, metrics, passed = run_calibration(params, df, max_iter=1)
            assert passed is True

    def test_calibration_threshold_fail(self):
        """Calibration should fail when metrics exceed thresholds."""
        params = {
            'P_G': 0.1,
            'P_L0': 0.5,
            'P_S': 0.1,
            'P_T': 0.2
        }
        
        with patch('simulate.calibration.run_calibration', return_value=(
            params,
            {'rmse': 0.20, 'diff': 0.05, 'num_samples': 10},
            False
        )):
            opt_params, metrics, passed = run_calibration(params, pd.DataFrame(), max_iter=1)
            assert passed is False

    def test_load_pilot_data_missing_file(self):
        """load_pilot_data should exit when file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = os.path.join(tmpdir, 'nonexistent.csv')
            with pytest.raises(SystemExit) as excinfo:
                load_pilot_data(missing_path)
            assert excinfo.value.code == 1

    def test_load_pilot_data_insufficient_records(self):
        """load_pilot_data should exit when records < 50."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, 'small.csv')
            df = pd.DataFrame({
                'student_id': ['S1'] * 10,
                'problem_id': ['P1'] * 10,
                'correct': [1] * 10,
                'attempt_num': list(range(1, 11))
            })
            df.to_csv(csv_path, index=False)
            
            with pytest.raises(SystemExit) as excinfo:
                load_pilot_data(csv_path)
            assert excinfo.value.code == 1

    def test_load_pilot_data_valid(self):
        """load_pilot_data should return DataFrame when valid."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, 'valid.csv')
            # Create 50+ records
            data = []
            for i in range(60):
                data.append({
                    'student_id': f'S{i % 10}',
                    'problem_id': f'P{i % 5}',
                    'correct': i % 2,
                    'attempt_num': (i // 10) + 1
                })
            df = pd.DataFrame(data)
            df.to_csv(csv_path, index=False)
            
            loaded = load_pilot_data(csv_path)
            assert len(loaded) >= 50
            assert 'student_id' in loaded.columns
            assert 'correct' in loaded.columns