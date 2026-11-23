import pytest
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd

# Adjust import path for local testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))
from simulate.calculate_calibration_metrics import (
    load_report,
    load_human_data,
    calculate_rmse_diff,
    run_metrics_check,
    RMSE_DIFF_THRESHOLD,
    RMSE_ABSOLUTE_THRESHOLD
)

class TestCalculateCalibrationMetrics:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test artifacts."""
        tmp = tempfile.mkdtemp()
        yield tmp
        shutil.rmtree(tmp)

    @pytest.fixture
    def mock_report(self, temp_dir):
        """Create a mock calibration report JSON."""
        report_path = os.path.join(temp_dir, 'calibration_report.json')
        data = {
            'rmse': 0.10,
            'data_source': 'human',
            'iterations': 100
        }
        with open(report_path, 'w') as f:
            json.dump(data, f)
        return report_path, data

    @pytest.fixture
    def mock_human_data(self, temp_dir):
        """Create a mock human pilot data CSV."""
        data_path = os.path.join(temp_dir, 'raw_pilot_data.csv')
        df = pd.DataFrame({
            'student_id': range(50),
            'problem_id': range(50),
            'correct': [1] * 50,
            'rt_seconds': [5.0] * 50
        })
        df.to_csv(data_path, index=False)
        return data_path

    def test_load_report_success(self, mock_report):
        path, _ = mock_report
        result = load_report(path)
        assert 'rmse' in result
        assert result['rmse'] == 0.10

    def test_load_report_not_found(self, temp_dir):
        with pytest.raises(FileNotFoundError):
            load_report(os.path.join(temp_dir, 'nonexistent.json'))

    def test_load_human_data_success(self, mock_human_data):
        df = load_human_data(mock_human_data)
        assert len(df) == 50
        assert 'student_id' in df.columns

    def test_load_human_data_not_found(self, temp_dir):
        with pytest.raises(FileNotFoundError):
            load_human_data(os.path.join(temp_dir, 'nonexistent.csv'))

    def test_calculate_rmse_diff(self, mock_report):
        _, report_data = mock_report
        diff = calculate_rmse_diff(report_data, baseline_rmse=0.05)
        expected = abs(0.10 - 0.05)
        assert diff == expected

    def test_calculate_rmse_diff_default_baseline(self, mock_report):
        _, report_data = mock_report
        diff = calculate_rmse_diff(report_data)
        assert diff == 0.10

    def test_metrics_pass_on_human_data(self, mock_report, mock_human_data, temp_dir):
        # Patch paths to use temp_dir
        report_path, _ = mock_report
        
        # Create a mock report with passing metrics
        passing_report = {
            'rmse': 0.10, # < 0.15
            'data_source': 'human'
        }
        with open(report_path, 'w') as f:
            json.dump(passing_report, f)

        # We need to patch the global constants and paths in the module
        # Since run_metrics_check uses module-level globals, we patch the function directly
        # or we mock the file system interactions.
        
        # Simpler approach: test the logic by mocking file reads and os.makedirs
        import simulate.calculate_calibration_metrics as mod

        with patch.object(mod, 'CALIBRATION_REPORT_PATH', report_path):
            with patch.object(mod, 'DATA_PILOT_DIR', temp_dir):
                with patch.object(mod, 'METRICS_OUTPUT_PATH', os.path.join(temp_dir, 'calibration_metrics.json')):
                    # This should not raise SystemExit
                    result = mod.run_metrics_check()
                    assert result == 0
                    
                    # Verify output file exists
                    metrics_path = os.path.join(temp_dir, 'calibration_metrics.json')
                    assert os.path.exists(metrics_path)
                    
                    with open(metrics_path, 'r') as f:
                        metrics = json.load(f)
                    
                    assert metrics['passed'] is True
                    assert metrics['rmse'] == 0.10

    def test_metrics_fail_on_human_data_rmse_diff(self, mock_report, mock_human_data, temp_dir):
        import simulate.calculate_calibration_metrics as mod

        # Create a report that fails the diff threshold
        failing_report = {
            'rmse': 0.05, # Difference from 0.0 baseline is 0.05 > 0.02
            'data_source': 'human'
        }
        
        with open(mock_report[0], 'w') as f:
            json.dump(failing_report, f)

        with patch.object(mod, 'CALIBRATION_REPORT_PATH', mock_report[0]):
            with patch.object(mod, 'DATA_PILOT_DIR', temp_dir):
                with patch.object(mod, 'METRICS_OUTPUT_PATH', os.path.join(temp_dir, 'calibration_metrics.json')):
                    # This should raise SystemExit(1)
                    with pytest.raises(SystemExit) as excinfo:
                        mod.run_metrics_check()
                    assert excinfo.value.code == 1

    def test_metrics_fail_on_human_data_absolute_rmse(self, mock_report, mock_human_data, temp_dir):
        import simulate.calculate_calibration_metrics as mod

        # Create a report that fails the absolute threshold
        failing_report = {
            'rmse': 0.20, # > 0.15
            'data_source': 'human'
        }
        
        with open(mock_report[0], 'w') as f:
            json.dump(failing_report, f)

        with patch.object(mod, 'CALIBRATION_REPORT_PATH', mock_report[0]):
            with patch.object(mod, 'DATA_PILOT_DIR', temp_dir):
                with patch.object(mod, 'METRICS_OUTPUT_PATH', os.path.join(temp_dir, 'calibration_metrics.json')):
                    with pytest.raises(SystemExit) as excinfo:
                        mod.run_metrics_check()
                    assert excinfo.value.code == 1

    def test_metrics_pass_on_synthetic_data(self, mock_report, mock_human_data, temp_dir):
        import simulate.calculate_calibration_metrics as mod

        # Synthetic data should not exit 1 even if thresholds are breached
        failing_report = {
            'rmse': 0.20, # > 0.15
            'data_source': 'synthetic'
        }
        
        with open(mock_report[0], 'w') as f:
            json.dump(failing_report, f)

        with patch.object(mod, 'CALIBRATION_REPORT_PATH', mock_report[0]):
            with patch.object(mod, 'DATA_PILOT_DIR', temp_dir):
                with patch.object(mod, 'METRICS_OUTPUT_PATH', os.path.join(temp_dir, 'calibration_metrics.json')):
                    # Should succeed (return 0) despite high RMSE
                    result = mod.run_metrics_check()
                    assert result == 0
                    
                    metrics_path = os.path.join(temp_dir, 'calibration_metrics.json')
                    with open(metrics_path, 'r') as f:
                        metrics = json.load(f)
                    
                    assert metrics['passed'] is False
                    assert 'synthetic' in metrics['reason'] or 'skipping' in metrics['reason'].lower()