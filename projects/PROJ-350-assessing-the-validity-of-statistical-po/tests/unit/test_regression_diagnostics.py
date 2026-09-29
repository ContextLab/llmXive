"""
Unit tests for regression_diagnostics.py (T027).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
import pytest
from scipy import stats

# Import the module functions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from regression_diagnostics import (
    load_power_analysis_data,
    filter_valid_power_gaps,
    perform_statistical_test,
    write_results,
    main
)

class TestLoadPowerAnalysisData:
    def test_load_valid_csv(self, tmp_path):
        csv_path = tmp_path / "test.csv"
        data = {"power_gap": [0.1, 0.2, 0.3], "other": [1, 2, 3]}
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        
        result = load_power_analysis_data(csv_path)
        assert len(result) == 3
        assert "power_gap" in result.columns
    
    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_power_analysis_data(tmp_path / "nonexistent.csv")
    
    def test_missing_column(self, tmp_path):
        csv_path = tmp_path / "test.csv"
        data = {"wrong_column": [1, 2, 3]}
        pd.DataFrame(data).to_csv(csv_path, index=False)
        
        with pytest.raises(ValueError) as exc_info:
            load_power_analysis_data(csv_path)
        assert "power_gap" in str(exc_info.value)

class TestFilterValidPowerGaps:
    def test_filter_nan_and_inf(self):
        data = pd.Series([0.1, np.nan, np.inf, -np.inf, 0.2, 0.3])
        result = filter_valid_power_gaps(pd.DataFrame({"power_gap": data}))
        assert len(result) == 3
        assert not result.isna().any()
        assert not np.isinf(result).any()
    
    def test_empty_after_filter(self):
        data = pd.Series([np.nan, np.inf, -np.inf])
        with pytest.raises(ValueError):
            filter_valid_power_gaps(pd.DataFrame({"power_gap": data}))

class TestPerformStatisticalTest:
    def test_t_test_normal_data(self):
        # Generate normal data centered at 0.5
        np.random.seed(42)
        sample = pd.Series(np.random.normal(loc=0.5, scale=0.1, size=50))
        result = perform_statistical_test(sample)
        
        assert result["test_type"] == "one_sample_t_test"
        assert result["is_normal"] is True
        assert result["p_value"] < 0.05 # Should be significant
        assert result["conclusion"] is not None
    
    def test_wilcoxon_non_normal_data(self, monkeypatch):
        # Force non-normality by mocking the normality test to return False
        sample = pd.Series([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
        
        # Mock Shapiro-Wilk to return p < 0.05
        original_shapiro = stats.shapiro
        def mock_shapiro(x):
            return 0.0, 0.001 # stat, p_val (p < 0.05)
        
        monkeypatch.setattr(stats, 'shapiro', mock_shapiro)
        
        result = perform_statistical_test(sample)
        
        assert result["test_type"] == "wilcoxon_signed_rank_test"
        assert result["is_normal"] is False
    
    def test_insufficient_data(self):
        sample = pd.Series([0.5])
        result = perform_statistical_test(sample)
        assert result["test_type"] == "insufficient_data"
        assert result["test_statistic"] is None
        assert result["p_value"] is None

class TestWriteResults:
    def test_write_json(self, tmp_path):
        output_path = tmp_path / "results.json"
        results = {"test": "value", "number": 123}
        
        write_results(results, output_path)
        
        assert output_path.exists()
        with open(output_path) as f:
            loaded = json.load(f)
        assert loaded["test"] == "value"
        assert loaded["number"] == 123

class TestMain:
    def test_main_success(self, tmp_path):
        # Setup mock data
        csv_path = tmp_path / "power_analysis.csv"
        data = {"power_gap": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]}
        pd.DataFrame(data).to_csv(csv_path, index=False)
        
        output_path = tmp_path / "regression_diagnostics.json"
        
        with patch("regression_diagnostics.INPUT_PATH", csv_path):
            with patch("regression_diagnostics.OUTPUT_PATH", output_path):
                exit_code = main()
        
        assert exit_code == 0
        assert output_path.exists()
    
    def test_main_file_not_found(self):
        with patch("regression_diagnostics.INPUT_PATH", Path("/nonexistent/path.csv")):
            exit_code = main()
        assert exit_code == 1