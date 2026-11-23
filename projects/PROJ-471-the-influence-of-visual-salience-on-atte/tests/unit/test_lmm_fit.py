"""
Unit tests for code/analysis/lmm_fit.py

Tests:
- Power gate check logic
- Data loading validation
- Model fitting (using mock data to avoid heavy computation)
- Result extraction
"""
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
import numpy as np

# Mock statsmodels before importing the module to avoid heavy imports in tests if needed,
# though for unit tests we usually test logic flow.
# Since we need to test the logic, we will mock the statsmodels return values.

# Add project root to path if not already
sys_path = Path(__file__).parent.parent.parent
if str(sys_path) not in os.sys.path:
    os.sys.path.insert(0, str(sys_path))

from analysis.lmm_fit import (
    check_power_gate,
    load_aligned_data,
    extract_results,
    main,
    POWER_GATE_FLAG_PATH,
    ALIGNED_DATA_PATH
)
from config import get_paths

class TestPowerGate:
    def test_no_flag_exists(self, tmp_path, monkeypatch):
        """Test that check returns True when no flag file exists."""
        # Setup mock paths
        paths = get_paths()
        # We need to mock get_paths to return our tmp_path structure
        # or just ensure the flag doesn't exist in the default location.
        # For simplicity, we assume default paths don't have the file in test env.
        
        # Simulate non-existence
        with patch('analysis.lmm_fit.get_paths') as mock_get_paths:
            mock_paths = MagicMock()
            mock_paths.data_interim = tmp_path
            mock_get_paths.return_value = mock_paths
            
            is_valid, reason = check_power_gate()
            assert is_valid is True
            assert reason is None

    def test_flag_exists_invalid(self, tmp_path, monkeypatch):
        """Test that check returns False when flag file exists."""
        flag_file = tmp_path / "invalid_for_inference_flag.json"
        flag_file.write_text(json.dumps({"reason": "Power too low"}))
        
        with patch('analysis.lmm_fit.get_paths') as mock_get_paths:
            mock_paths = MagicMock()
            mock_paths.data_interim = tmp_path
            mock_get_paths.return_value = mock_paths
            
            is_valid, reason = check_power_gate()
            assert is_valid is False
            assert "Power too low" in reason

class TestLoadData:
    def test_load_valid_data(self, tmp_path, monkeypatch):
        """Test loading a valid CSV."""
        data_file = tmp_path / "aligned_metrics.csv"
        df_mock = pd.DataFrame({
            'TrialID': [1, 2, 3],
            'SubjectID': ['S1', 'S1', 'S2'],
            'SalienceScore': [0.1, 0.5, 0.8],
            'DwellTime': [100, 200, 150],
            'FirstFixationProb': [0.5, 0.8, 0.9]
        })
        df_mock.to_csv(data_file, index=False)
        
        with patch('analysis.lmm_fit.get_paths') as mock_get_paths:
            mock_paths = MagicMock()
            mock_paths.data_processed = tmp_path
            mock_get_paths.return_value = mock_paths
            
            df = load_aligned_data()
            assert len(df) == 3
            assert 'SalienceScore' in df.columns

    def test_missing_columns(self, tmp_path, monkeypatch):
        """Test error when columns are missing."""
        data_file = tmp_path / "aligned_metrics.csv"
        df_mock = pd.DataFrame({
            'TrialID': [1],
            'WrongColumn': [0.5]
        })
        df_mock.to_csv(data_file, index=False)
        
        with patch('analysis.lmm_fit.get_paths') as mock_get_paths:
            mock_paths = MagicMock()
            mock_paths.data_processed = tmp_path
            mock_get_paths.return_value = mock_paths
            
            with pytest.raises(ValueError):
                load_aligned_data()

class TestExtractResults:
    def test_extract_success(self):
        """Test extracting results from a mock statsmodels result object."""
        mock_result = MagicMock()
        mock_result.params = {'SalienceScore': 0.5, 'Intercept': 10.0}
        mock_result.pvalues = {'SalienceScore': 0.01, 'Intercept': 0.001}
        mock_result.bse = {'SalienceScore': 0.1, 'Intercept': 1.0}
        mock_result.tvalues = {'SalienceScore': 5.0}
        mock_result.conf_int = MagicMock(return_value=pd.DataFrame([[0.3, 0.7], [8.0, 12.0]], index=['SalienceScore', 'Intercept']))
        mock_result.llf = 100.0
        mock_result.aic = 204.0
        mock_result.bic = 210.0

        res = extract_results(mock_result)
        
        assert res['status'] == 'success'
        assert res['coefficient'] == 0.5
        assert res['p_value'] == 0.01
        assert res['confidence_interval'] == [0.3, 0.7]

    def test_extract_none(self):
        """Test handling of None result."""
        res = extract_results(None)
        assert res['status'] == 'failed'

class TestMain:
    @patch('analysis.lmm_fit.check_power_gate')
    @patch('analysis.lmm_fit.load_aligned_data')
    @patch('analysis.lmm_fit.fit_model_a')
    @patch('analysis.lmm_fit.fit_model_b')
    @patch('analysis.lmm_fit.write_final_results')
    def test_main_success(
        self, mock_write, mock_fit_b, mock_fit_a, mock_load, mock_check, tmp_path, monkeypatch
    ):
        """Test main execution flow on success."""
        mock_check.return_value = (True, None)
        mock_load.return_value = pd.DataFrame({'TrialID': [1], 'SubjectID': ['S1'], 'SalienceScore': [0.5], 'DwellTime': [100], 'FirstFixationProb': [0.5]})
        mock_fit_a.return_value = (MagicMock(), "Summary A")
        mock_fit_b.return_value = (MagicMock(), "Summary B")
        
        # Mock get_paths to return tmp_path for output
        with patch('analysis.lmm_fit.get_paths') as mock_paths:
            p = MagicMock()
            p.data_processed = tmp_path
            mock_paths.return_value = p
            
            result = main()
            assert result == 0
            mock_write.assert_called_once()

    @patch('analysis.lmm_fit.check_power_gate')
    def test_main_power_gate_fail(self, mock_check, tmp_path, monkeypatch):
        """Test main execution flow when power gate fails."""
        mock_check.return_value = (False, "Power < 0.8")
        
        with patch('analysis.lmm_fit.get_paths') as mock_paths:
            p = MagicMock()
            p.data_processed = tmp_path
            mock_paths.return_value = p
            
            result = main()
            assert result == 1
            # Verify error report was written
            report_path = tmp_path / "results.json"
            assert report_path.exists()