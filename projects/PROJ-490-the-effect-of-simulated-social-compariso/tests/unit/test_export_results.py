import os
import json
import tempfile
from pathlib import Path
import pandas as pd
import pytest
import numpy as np

from code.analysis.export_results import export_regression_results, run_export
from code.utils.validators import validate_output

class TestExportResults:
    """Unit tests for regression result export functionality."""

    @pytest.fixture
    def sample_coefficients(self):
        """Create sample regression coefficients DataFrame."""
        data = {
            'term': ['intercept', 'avatar_condition', 'pre_self_esteem', 
                    'comparison_tendency', 'interaction'],
            'estimate': [2.5, 0.3, 0.8, -0.2, 0.15],
            'std_error': [0.1, 0.05, 0.08, 0.06, 0.04],
            't_value': [25.0, 6.0, 10.0, -3.33, 3.75],
            'p_value': [0.0, 0.0001, 0.0, 0.001, 0.0005]
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def sample_diagnostics(self):
        """Create sample model diagnostics dictionary."""
        return {
            'normality': {
                'statistic': 0.98,
                'p_value': 0.45,
                'passed': True
            },
            'homoscedasticity': {
                'statistic': 2.1,
                'p_value': 0.15,
                'passed': True
            },
            'vif': {
                'avatar_condition': 1.2,
                'pre_self_esteem': 1.5,
                'comparison_tendency': 1.3,
                'interaction': 1.4
            },
            'confidence_intervals': {
                'avatar_condition': [0.2, 0.4],
                'pre_self_esteem': [0.65, 0.95],
                'comparison_tendency': [-0.32, -0.08],
                'interaction': [0.07, 0.23]
            },
            'model_fit': {
                'r_squared': 0.65,
                'adj_r_squared': 0.63,
                'f_statistic': 45.2,
                'f_p_value': 0.0
            }
        }

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_export_creates_files(self, sample_coefficients, sample_diagnostics, temp_output_dir):
        """Test that export creates both CSV and JSON files."""
        csv_path, json_path = export_regression_results(
            coefficients_df=sample_coefficients,
            diagnostics_dict=sample_diagnostics,
            output_dir=temp_output_dir,
            data_source_type="real"
        )

        assert csv_path.exists(), "CSV file should be created"
        assert json_path.exists(), "JSON file should be created"
        assert csv_path.suffix == ".csv"
        assert json_path.suffix == ".json"

    def test_csv_content(self, sample_coefficients, temp_output_dir):
        """Test that CSV file contains correct data."""
        csv_path, _ = export_regression_results(
            coefficients_df=sample_coefficients,
            diagnostics_dict={},
            output_dir=temp_output_dir
        )

        df = pd.read_csv(csv_path)
        pd.testing.assert_frame_equal(df, sample_coefficients)

    def test_json_structure(self, sample_coefficients, sample_diagnostics, temp_output_dir):
        """Test that JSON file has correct structure."""
        _, json_path = export_regression_results(
            coefficients_df=sample_coefficients,
            diagnostics_dict=sample_diagnostics,
            output_dir=temp_output_dir
        )

        with open(json_path, 'r') as f:
            data = json.load(f)

        assert 'metadata' in data
        assert 'assumption_tests' in data
        assert 'collinearity' in data
        assert 'confidence_intervals' in data
        assert 'model_fit' in data

    def test_metadata_fields(self, sample_coefficients, sample_diagnostics, temp_output_dir):
        """Test that metadata contains required fields."""
        _, json_path = export_regression_results(
            coefficients_df=sample_coefficients,
            diagnostics_dict=sample_diagnostics,
            output_dir=temp_output_dir,
            data_source_type="synthetic"
        )

        with open(json_path, 'r') as f:
            data = json.load(f)

        assert data['metadata']['data_source_type'] == "synthetic"
        assert 'export_timestamp' in data['metadata']
        assert data['metadata']['model_type'] == "ANCOVA"

    def test_vif_flagging(self, sample_coefficients, sample_diagnostics, temp_output_dir):
        """Test that VIF values >= 5 are flagged."""
        high_vif_diagnostics = sample_diagnostics.copy()
        high_vif_diagnostics['vif'] = {
            'avatar_condition': 1.2,
            'pre_self_esteem': 6.5,  # High VIF
            'comparison_tendency': 1.3,
            'interaction': 1.4
        }

        _, json_path = export_regression_results(
            coefficients_df=sample_coefficients,
            diagnostics_dict=high_vif_diagnostics,
            output_dir=temp_output_dir
        )

        with open(json_path, 'r') as f:
            data = json.load(f)

        assert data['collinearity']['max_vif'] == 6.5
        assert data['collinearity']['flagged'] is True

    def test_run_export_wrapper(self, sample_coefficients, sample_diagnostics, temp_output_dir):
        """Test the run_export wrapper function."""
        csv_path, json_path = run_export(
            coefficients_df=sample_coefficients,
            diagnostics_dict=sample_diagnostics,
            output_dir=temp_output_dir,
            data_source_type="real"
        )

        assert csv_path.exists()
        assert json_path.exists()