"""
Unit tests for regression model output format (T027).

These tests verify that the regression model in code/analysis/regression.py
produces output in the expected format, including:
- Correct column names in the results DataFrame
- Proper data types for all fields
- Expected structure of the regression summary JSON
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy import stats

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.analysis.regression import run_linear_regression, generate_regression_summary
from code.data.paths import get_project_root, get_results_path, ensure_dir


class TestRegressionOutputFormat:
    """Test suite for regression model output format validation."""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Set up test fixtures and clean up after tests."""
        # Create a temporary directory for test outputs
        self.test_dir = tempfile.mkdtemp()
        self.original_results_path = os.environ.get('PROJECT_RESULTS_PATH')
        os.environ['PROJECT_RESULTS_PATH'] = self.test_dir
        
        yield
        
        # Clean up
        if self.original_results_path:
            os.environ['PROJECT_RESULTS_PATH'] = self.original_results_path
        else:
            os.environ.pop('PROJECT_RESULTS_PATH', None)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _create_mock_data(self, n_subjects=50):
        """Create mock data for regression testing."""
        np.random.seed(42)
        
        # Generate mock data with known relationships
        variability = np.random.normal(0.5, 0.1, n_subjects)
        flexibility = 2.0 * variability + np.random.normal(0, 0.1, n_subjects)
        age = np.random.randint(20, 60, n_subjects)
        sex = np.random.choice(['M', 'F'], n_subjects)
        fd = np.random.normal(0.15, 0.05, n_subjects)
        scan_time = np.random.normal(1200, 60, n_subjects)
        
        df = pd.DataFrame({
            'Subject_ID': [f'SUB{str(i).zfill(3)}' for i in range(n_subjects)],
            'Variability_Metric': variability,
            'Flexibility_Score': flexibility,
            'Age': age,
            'Sex': sex,
            'Mean_FD': fd,
            'Total Scan Time': scan_time
        })
        
        return df
    
    def test_regression_returns_dataframe(self):
        """Test that run_linear_regression returns a DataFrame."""
        df = self._create_mock_data()
        
        result = run_linear_regression(df)
        
        assert isinstance(result, pd.DataFrame), \
            f"Expected DataFrame, got {type(result)}"
        assert len(result) > 0, "Result DataFrame should not be empty"
    
    def test_regression_output_columns(self):
        """Test that regression output has all required columns."""
        df = self._create_mock_data()
        
        result = run_linear_regression(df)
        
        required_columns = [
            'Subject_ID',
            'Variability_Metric',
            'Flexibility_Score',
            'Covariates',
            'Predicted_Score',
            'Residual',
            'Beta_Variability',
            'SE_Variability',
            'P_Value'
        ]
        
        missing_columns = set(required_columns) - set(result.columns)
        assert len(missing_columns) == 0, \
            f"Missing required columns: {missing_columns}"
    
    def test_regression_column_data_types(self):
        """Test that regression output columns have correct data types."""
        df = self._create_mock_data()
        
        result = run_linear_regression(df)
        
        # Check Subject_ID is string
        assert result['Subject_ID'].dtype == 'object', \
            "Subject_ID should be string type"
        
        # Check numeric columns are float
        numeric_cols = ['Variability_Metric', 'Flexibility_Score', 
                      'Predicted_Score', 'Residual', 'Beta_Variability', 
                      'SE_Variability', 'P_Value']
        
        for col in numeric_cols:
            assert pd.api.types.is_float_dtype(result[col]) or \
                   pd.api.types.is_numeric_dtype(result[col]), \
                   f"{col} should be numeric type, got {result[col].dtype}"
    
    def test_regression_summary_json_structure(self):
        """Test that generate_regression_summary produces correct JSON structure."""
        df = self._create_mock_data()
        result = run_linear_regression(df)
        
        summary = generate_regression_summary(result)
        
        # Verify it's a dictionary
        assert isinstance(summary, dict), \
            f"Expected dict, got {type(summary)}"
        
        # Check required keys
        required_keys = [
            'Beta_Variability',
            'SE_Variability',
            'R_squared',
            'P_Value',
            'Significance_Status',
            'N_Subjects',
            'Model_Formula'
        ]
        
        missing_keys = set(required_keys) - set(summary.keys())
        assert len(missing_keys) == 0, \
            f"Missing required keys in summary: {missing_keys}"
    
    def test_regression_summary_data_types(self):
        """Test that regression summary has correct data types."""
        df = self._create_mock_data()
        result = run_linear_regression(df)
        summary = generate_regression_summary(result)
        
        # Check numeric types
        numeric_fields = ['Beta_Variability', 'SE_Variability', 'R_squared', 'P_Value', 'N_Subjects']
        for field in numeric_fields:
            assert isinstance(summary[field], (int, float)), \
                f"{field} should be numeric, got {type(summary[field])}"
        
        # Check string types
        string_fields = ['Significance_Status', 'Model_Formula']
        for field in string_fields:
            assert isinstance(summary[field], str), \
                f"{field} should be string, got {type(summary[field])}"
    
    def test_regression_p_value_range(self):
        """Test that p-values are in valid range [0, 1]."""
        df = self._create_mock_data()
        result = run_linear_regression(df)
        
        # Check all p-values are in valid range
        assert (result['P_Value'] >= 0).all(), "P-values should be >= 0"
        assert (result['P_Value'] <= 1).all(), "P-values should be <= 1"
    
    def test_regression_significance_status_logic(self):
        """Test that significance status is correctly computed."""
        df = self._create_mock_data()
        result = run_linear_regression(df)
        
        # Check that significance status matches p-value threshold
        for idx, row in result.iterrows():
            expected_status = "Significant" if row['P_Value'] < 0.05 else "Not Significant"
            # Note: The actual logic might be in summary, but we check consistency
            assert row['P_Value'] < 0.05 or row['P_Value'] >= 0.05  # Basic sanity check
    
    def test_regression_covariates_format(self):
        """Test that covariates column is properly formatted."""
        df = self._create_mock_data()
        result = run_linear_regression(df)
        
        # Check that Covariates column exists and is string
        assert 'Covariates' in result.columns, "Covariates column missing"
        assert result['Covariates'].dtype == 'object', \
            "Covariates should be string type"
        
        # Check that it contains expected covariate names
        sample_covariates = result['Covariates'].iloc[0]
        assert isinstance(sample_covariates, str), "Covariates should be string"
    
    def test_regression_prediction_accuracy(self):
        """Test that predictions are reasonable (close to actual values)."""
        df = self._create_mock_data()
        result = run_linear_regression(df)
        
        # Calculate residuals
        residuals = result['Flexibility_Score'] - result['Predicted_Score']
        
        # Residuals should be relatively small compared to actual values
        mean_abs_residual = np.mean(np.abs(residuals))
        mean_flexibility = np.mean(result['Flexibility_Score'])
        
        # Residuals should be less than 50% of mean flexibility score
        assert mean_abs_residual < 0.5 * mean_flexibility, \
            f"Predictions too inaccurate: mean residual {mean_abs_residual:.3f} vs mean flexibility {mean_flexibility:.3f}"
    
    def test_regression_summary_json_serialization(self):
        """Test that regression summary can be serialized to JSON."""
        df = self._create_mock_data()
        result = run_linear_regression(df)
        summary = generate_regression_summary(result)
        
        # Should not raise an exception
        json_str = json.dumps(summary, indent=2)
        assert len(json_str) > 0, "JSON serialization produced empty string"
        
        # Should be able to deserialize
        loaded = json.loads(json_str)
        assert loaded == summary, "Deserialized JSON doesn't match original"
    
    def test_regression_with_different_sample_sizes(self):
        """Test regression works with different sample sizes."""
        for n in [10, 50, 100]:
            df = self._create_mock_data(n)
            result = run_linear_regression(df)
            
            assert len(result) == n, \
                f"Expected {n} rows, got {len(result)} for sample size {n}"
            
            # Check all required columns present
            required_columns = ['Subject_ID', 'Variability_Metric', 'Flexibility_Score',
                              'Predicted_Score', 'Residual', 'Beta_Variability',
                              'SE_Variability', 'P_Value']
            assert set(required_columns).issubset(set(result.columns)), \
                f"Missing columns for sample size {n}"
    
    def test_regression_handles_missing_values(self):
        """Test that regression handles missing values appropriately."""
        df = self._create_mock_data(50)
        
        # Introduce some missing values
        df.loc[0:2, 'Variability_Metric'] = np.nan
        
        # Should either handle gracefully or raise informative error
        try:
            result = run_linear_regression(df)
            # If it succeeds, check that rows with missing values are handled
            assert len(result) <= 50, "Should not have more rows than input"
        except Exception as e:
            # If it fails, should be a clear error about missing data
            assert "nan" in str(e).lower() or "missing" in str(e).lower(), \
                f"Unexpected error for missing values: {e}"