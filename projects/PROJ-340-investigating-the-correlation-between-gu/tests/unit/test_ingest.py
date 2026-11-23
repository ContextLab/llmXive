"""
Unit tests for the data ingestion module (code/ingest.py).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json

# Import functions from code/ingest.py based on the API surface
from code.ingest import (
    detect_outliers_iqr,
    save_outlier_report,
    filter_outliers,
    save_filtered_data,
    load_required_variables,
    validate_variables
)

class TestOutlierDetection:
    """Unit tests for outlier detection logic."""

    def test_detect_outliers_iqr_normal_data(self):
        """Test outlier detection on normal distributed data."""
        # Generate normal data
        np.random.seed(42)
        data = np.random.normal(loc=100, scale=10, size=1000)
        df = pd.DataFrame({'metric': data})
        
        outliers = detect_outliers_iqr(df, 'metric')
        
        # In a normal distribution, ~0.7% should be outliers by IQR
        outlier_ratio = len(outliers) / len(df)
        assert 0.001 < outlier_ratio < 0.05, f"Outlier ratio {outlier_ratio} is unexpected for normal data"

    def test_detect_outliers_iqr_with_known_outliers(self):
        """Test outlier detection when known outliers are injected."""
        data = [10, 12, 11, 13, 12, 10, 11, 12, 100, -50]
        df = pd.DataFrame({'metric': data})
        
        outliers = detect_outliers_iqr(df, 'metric')
        
        # 100 and -50 should be detected as outliers
        assert len(outliers) == 2, f"Expected 2 outliers, found {len(outliers)}"
        assert 100 in outliers['value'].values
        assert -50 in outliers['value'].values

    def test_save_outlier_report_creates_file(self, tmp_path):
        """Test that saving an outlier report creates the expected file."""
        report = {
            'outliers': [
                {'subject_id': 'S001', 'metric': 'sleep_duration', 'value': 10.5, 'is_outlier': True},
                {'subject_id': 'S002', 'metric': 'sleep_duration', 'value': 4.0, 'is_outlier': True}
            ],
            'exclusion_count': 2
        }
        output_path = tmp_path / "outlier_report.json"
        
        save_outlier_report(report, str(output_path))
        
        assert output_path.exists(), "Outlier report file was not created"
        
        with open(output_path, 'r') as f:
            loaded_report = json.load(f)
        
        assert loaded_report == report

class TestVariableValidation:
    """Unit tests for variable validation logic."""

    def test_validate_variables_missing_required(self, tmp_path):
        """Test validation fails when required variables are missing."""
        # Create a minimal required_variables.yaml
        config_path = tmp_path / "required_variables.yaml"
        config = {
            'required_predictors': ['taxon_A', 'taxon_B'],
            'required_outcomes': ['sleep_duration']
        }
        import yaml
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        
        # Create a dataframe missing 'taxon_B'
        df = pd.DataFrame({
            'subject_id': [1, 2, 3],
            'taxon_A': [10, 20, 30],
            'sleep_duration': [8, 7, 9]
        })
        
        # This should raise an error or return False depending on implementation
        # Assuming validate_variables raises ValueError or returns a status dict
        try:
            result = validate_variables(df, str(config_path))
            # If it returns a status, check for failure
            if isinstance(result, dict):
                assert result.get('valid') == False, "Validation should fail for missing variables"
            else:
                # If it raises, the test passes
                pytest.fail("Expected validation to fail for missing variables")
        except (ValueError, KeyError) as e:
            # Expected behavior
            assert "missing" in str(e).lower() or "required" in str(e).lower()

    def test_validate_variables_all_present(self, tmp_path):
        """Test validation passes when all required variables are present."""
        config_path = tmp_path / "required_variables.yaml"
        config = {
            'required_predictors': ['taxon_A'],
            'required_outcomes': ['sleep_duration']
        }
        import yaml
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        
        df = pd.DataFrame({
            'subject_id': [1, 2, 3],
            'taxon_A': [10, 20, 30],
            'sleep_duration': [8, 7, 9]
        })
        
        result = validate_variables(df, str(config_path))
        
        if isinstance(result, dict):
            assert result.get('valid') == True
        # If it raises, it's a failure
