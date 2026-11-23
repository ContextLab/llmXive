import pytest
import os
import json
import tempfile
import numpy as np
import pandas as pd
from pathlib import Path
from src.utils.scaling_analyzer import (
    load_scaling_data,
    perform_log_log_regression,
    classify_trend,
    generate_scaling_law_report
)

class TestScalingAnalyzer:
    
    @pytest.fixture
    def sample_scaling_csv(self, tmp_path):
        """Create a sample scaling_law.csv file for testing."""
        csv_path = tmp_path / "scaling_law.csv"
        data = {
            'columns': [1, 2, 4],
            'params': [1000000, 2000000, 4000000],
            'mae': [0.15, 0.10, 0.07],
            'time_sec': [100, 200, 400]
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        return str(csv_path)
    
    def test_load_scaling_data(self, sample_scaling_csv):
        """Test loading scaling data from CSV."""
        params, mae = load_scaling_data(sample_scaling_csv)
        
        assert len(params) == 3
        assert len(mae) == 3
        assert np.allclose(params, [1000000, 2000000, 4000000])
        assert np.allclose(mae, [0.15, 0.10, 0.07])
    
    def test_load_scaling_data_missing_file(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_scaling_data("/nonexistent/path.csv")
    
    def test_load_scaling_data_missing_column(self, tmp_path):
        """Test that ValueError is raised for missing required column."""
        csv_path = tmp_path / "bad_scaling.csv"
        data = {
            'columns': [1, 2, 4],
            'time_sec': [100, 200, 400]
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)
        
        with pytest.raises(ValueError, match="Missing required column"):
            load_scaling_data(str(csv_path))
    
    def test_perform_log_log_regression(self, sample_scaling_csv):
        """Test log-log regression calculation."""
        params, mae = load_scaling_data(sample_scaling_csv)
        results = perform_log_log_regression(params, mae)
        
        assert 'beta' in results
        assert 'intercept' in results
        assert 'r_squared' in results
        assert 'p_value' in results
        assert 'std_err' in results
        
        # All values should be floats
        assert isinstance(results['beta'], float)
        assert isinstance(results['r_squared'], float)
        
        # R-squared should be between 0 and 1
        assert 0 <= results['r_squared'] <= 1
        
        # For this data, we expect a negative beta (sublinear)
        assert results['beta'] < 0
    
    def test_classify_trend_sublinear(self):
        """Test trend classification for sublinear scaling."""
        assert classify_trend(-0.5) == "sublinear"
        assert classify_trend(-0.1) == "sublinear"
        assert classify_trend(-1.0) == "sublinear"
    
    def test_classify_trend_linear(self):
        """Test trend classification for linear scaling."""
        assert classify_trend(0.0) == "linear"
        assert classify_trend(0.05) == "linear"
        assert classify_trend(-0.05) == "linear"
    
    def test_classify_trend_superlinear(self):
        """Test trend classification for superlinear scaling."""
        assert classify_trend(0.5) == "superlinear"
        assert classify_trend(0.1) == "superlinear"
        assert classify_trend(1.0) == "superlinear"
    
    def test_generate_scaling_law_report(self, sample_scaling_csv, tmp_path):
        """Test report generation."""
        params, mae = load_scaling_data(sample_scaling_csv)
        regression_results = perform_log_log_regression(params, mae)
        trend_type = classify_trend(regression_results['beta'])
        
        output_path = tmp_path / "scaling_law_report.md"
        generate_scaling_law_report(
            csv_path=sample_scaling_csv,
            output_path=str(output_path),
            regression_results=regression_results,
            trend_type=trend_type,
            metric_used="MAE"
        )
        
        # Verify file was created
        assert output_path.exists()
        
        # Verify content
        with open(output_path, 'r') as f:
            content = f.read()
        
        assert "Scaling Law Analysis Report" in content
        assert "MAE" in content
        assert "Scaling Exponent" in content
        assert trend_type in content
        assert str(regression_results['beta']) in content
    
    def test_generate_scaling_law_report_creates_directory(self, sample_scaling_csv, tmp_path):
        """Test that report generation creates output directory if needed."""
        params, mae = load_scaling_data(sample_scaling_csv)
        regression_results = perform_log_log_regression(params, mae)
        trend_type = classify_trend(regression_results['beta'])
        
        output_path = tmp_path / "subdir" / "nested" / "report.md"
        generate_scaling_law_report(
            csv_path=sample_scaling_csv,
            output_path=str(output_path),
            regression_results=regression_results,
            trend_type=trend_type,
            metric_used="MAE"
        )
        
        assert output_path.exists()
    
    def test_regression_results_structure(self, sample_scaling_csv):
        """Test that regression results have correct structure and types."""
        params, mae = load_scaling_data(sample_scaling_csv)
        results = perform_log_log_regression(params, mae)
        
        required_keys = ['beta', 'intercept', 'r_squared', 'p_value', 'std_err']
        for key in required_keys:
            assert key in results
            assert isinstance(results[key], float)
    
    def test_trend_classification_matches_beta(self):
        """Test that trend classification correctly matches beta value."""
        test_cases = [
            (-0.5, "sublinear"),
            (-0.01, "linear"),
            (0.0, "linear"),
            (0.01, "linear"),
            (0.5, "superlinear"),
        ]
        
        for beta, expected_trend in test_cases:
            actual_trend = classify_trend(beta)
            assert actual_trend == expected_trend, f"Failed for beta={beta}"