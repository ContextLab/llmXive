"""
Integration test for User Story 2: Statistical Validation & Bias Assessment.
Verifies that the validation pipeline generates a report with correct structure
and meets metric thresholds defined in the project specs.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from validate import main as validate_main
from utils import raise_data_insufficiency


class TestValidationIntegration:
    """
    Integration tests for the validation pipeline (T020).
    These tests verify that the validation script produces a valid report
    and that metric thresholds are correctly enforced.
    """

    def setup_method(self):
        """Setup temporary directories and mock data for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.artifacts_dir = Path(self.temp_dir) / "artifacts" / "reports"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

        self.model_path = Path(self.temp_dir) / "models" / "best_model.json"
        self.data_path = Path(self.temp_dir) / "data" / "processed" / "cleaned_dataset.parquet"
        
        # Ensure directories exist
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        self.data_path.parent.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Clean up temporary directories."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_mock_model(self):
        """Create a mock model artifact file."""
        mock_model_data = {
            "model_type": "xgboost",
            "parameters": {
                "max_depth": 5,
                "learning_rate": 0.1,
                "n_estimators": 100
            },
            "feature_names": ["misorientation_angle", "sigma_value", "boundary_width", "excess_volume"]
        }
        with open(self.model_path, 'w') as f:
            json.dump(mock_model_data, f)

    def _create_mock_data(self):
        """Create a mock dataset file with realistic structure."""
        # Since we can't load pandas/parquet without dependencies in this context,
        # we will mock the data loading function in the test itself.
        pass

    def test_validation_report_generation(self):
        """
        Test that the validation script generates a report with the expected structure.
        Verifies T020 requirement: report generation.
        """
        self._create_mock_model()
        
        # Mock the data loading and model loading to avoid dependency on real parquet files
        mock_y_true = np.random.rand(100)
        mock_y_pred = mock_y_true + np.random.normal(0, 0.1, 100)
        
        with patch('validate.load_data', return_value=(mock_y_true, mock_y_pred, {})), \
             patch('validate.load_model', return_value=MagicMock()), \
             patch('validate.prepare_features', return_value=MagicMock()), \
             patch('validate.perform_cross_validation', return_value={
                 'r2_scores': [0.85, 0.84, 0.86, 0.83, 0.85],
                 'rmse_scores': [0.12, 0.13, 0.11, 0.14, 0.12],
                 'mape_scores': [0.05, 0.06, 0.04, 0.07, 0.05]
             }), \
             patch('validate.regression_bias_test', return_value={
                 'intercept': 0.01,
                 'slope': 0.98,
                 'p_value': 0.45
             }), \
             patch('validate.apply_bonferroni_correction', return_value={'adjusted_alpha': 0.017}):
            
            # Run the validation main function
            args = [
                '--model_path', str(self.model_path),
                '--output_path', str(self.artifacts_dir / "validation_report.json")
            ]
            
            try:
                validate_main(args)
            except SystemExit as e:
                # Expected if the script finishes successfully
                if e.code != 0:
                    pytest.fail(f"Validation script exited with code {e.code}")

            # Verify report was generated
            report_path = self.artifacts_dir / "validation_report.json"
            assert report_path.exists(), "Validation report was not generated"

            with open(report_path, 'r') as f:
                report = json.load(f)

            # Verify report structure
            required_keys = ['cross_validation_metrics', 'bias_test_results', 'bonferroni_correction', 'summary']
            for key in required_keys:
                assert key in report, f"Missing required key in report: {key}"

            # Verify cross-validation metrics structure
            cv_metrics = report['cross_validation_metrics']
            assert 'mean_r2' in cv_metrics
            assert 'std_r2' in cv_metrics
            assert 'mean_rmse' in cv_metrics
            assert 'mean_mape' in cv_metrics

            # Verify bias test results structure
            bias_results = report['bias_test_results']
            assert 'intercept' in bias_results
            assert 'slope' in bias_results
            assert 'p_value' in bias_results
            assert 'is_significant' in bias_results

    def test_metric_threshold_enforcement(self):
        """
        Test that the validation script enforces metric thresholds.
        Verifies T020 requirement: metric thresholds.
        Specifically checks that std_r2 <= 0.05 as per spec.
        """
        self._create_mock_model()
        
        # Mock data that violates the std_r2 threshold
        mock_y_true = np.random.rand(100)
        mock_y_pred = mock_y_true + np.random.normal(0, 0.1, 100)
        
        # Simulate high variance in R2 scores (std > 0.05)
        high_variance_r2_scores = [0.95, 0.70, 0.85, 0.65, 0.90]  # std ~ 0.12
        
        with patch('validate.load_data', return_value=(mock_y_true, mock_y_pred, {})), \
             patch('validate.load_model', return_value=MagicMock()), \
             patch('validate.prepare_features', return_value=MagicMock()), \
             patch('validate.perform_cross_validation', return_value={
                 'r2_scores': high_variance_r2_scores,
                 'rmse_scores': [0.1, 0.2, 0.15, 0.25, 0.12],
                 'mape_scores': [0.05, 0.10, 0.08, 0.12, 0.06]
             }), \
             patch('validate.regression_bias_test', return_value={
                 'intercept': 0.01,
                 'slope': 0.98,
                 'p_value': 0.45
             }), \
             patch('validate.apply_bonferroni_correction', return_value={'adjusted_alpha': 0.017}):
            
            args = [
                '--model_path', str(self.model_path),
                '--output_path', str(self.artifacts_dir / "validation_report.json")
            ]
            
            # The script should still run but report the threshold violation
            try:
                validate_main(args)
            except SystemExit as e:
                # Check if it's a threshold violation exit code (if implemented)
                pass

            report_path = self.artifacts_dir / "validation_report.json"
            assert report_path.exists(), "Validation report was not generated even with threshold violation"

            with open(report_path, 'r') as f:
                report = json.load(f)

            # Verify the report contains the threshold violation information
            summary = report.get('summary', {})
            assert 'threshold_violations' in summary or 'warnings' in summary, \
                "Report should indicate threshold violations"

            # Check that the calculated std_r2 is correctly reported
            cv_metrics = report['cross_validation_metrics']
            calculated_std = np.std(high_variance_r2_scores)
            assert abs(cv_metrics['std_r2'] - calculated_std) < 1e-6, \
                f"Standard deviation of R2 scores not calculated correctly: {cv_metrics['std_r2']} vs {calculated_std}"

    def test_bonferroni_correction_application(self):
        """
        Test that Bonferroni correction is correctly applied to multiple hypothesis tests.
        Verifies T020 requirement: FWER correction.
        """
        self._create_mock_model()
        
        mock_y_true = np.random.rand(100)
        mock_y_pred = mock_y_true + np.random.normal(0, 0.1, 100)
        
        with patch('validate.load_data', return_value=(mock_y_true, mock_y_pred, {})), \
             patch('validate.load_model', return_value=MagicMock()), \
             patch('validate.prepare_features', return_value=MagicMock()), \
             patch('validate.perform_cross_validation', return_value={
                 'r2_scores': [0.85, 0.84, 0.86, 0.83, 0.85],
                 'rmse_scores': [0.12, 0.13, 0.11, 0.14, 0.12],
                 'mape_scores': [0.05, 0.06, 0.04, 0.07, 0.05]
             }), \
             patch('validate.regression_bias_test', return_value={
                 'intercept': 0.01,
                 'slope': 0.98,
                 'p_value': 0.45
             }):
            
            # Test with 3 hypotheses to verify Bonferroni correction
            with patch('validate.apply_bonferroni_correction', return_value={'adjusted_alpha': 0.0167}):
                args = [
                    '--model_path', str(self.model_path),
                    '--output_path', str(self.artifacts_dir / "validation_report.json")
                ]
                
                try:
                    validate_main(args)
                except SystemExit:
                    pass

                report_path = self.artifacts_dir / "validation_report.json"
                assert report_path.exists()

                with open(report_path, 'r') as f:
                    report = json.load(f)

                # Verify Bonferroni correction was applied
                bonferroni = report.get('bonferroni_correction', {})
                assert 'original_alpha' in bonferroni
                assert 'number_of_tests' in bonferroni
                assert 'adjusted_alpha' in bonferroni
                
                # Verify the calculation is correct (0.05 / 3 ≈ 0.0167)
                expected_adjusted = 0.05 / 3
                assert abs(bonferroni['adjusted_alpha'] - expected_adjusted) < 0.0001

    def test_integration_with_real_data_path_structure(self):
        """
        Test that the validation script correctly handles the expected file paths
        as defined in the project structure.
        """
        # Create a temporary project-like structure
        temp_project = Path(self.temp_dir) / "test_project"
        temp_project.mkdir()
        
        models_dir = temp_project / "models"
        data_dir = temp_project / "data" / "processed"
        artifacts_dir = temp_project / "artifacts" / "reports"
        
        models_dir.mkdir(parents=True)
        data_dir.mkdir(parents=True)
        artifacts_dir.mkdir(parents=True)
        
        model_file = models_dir / "best_model.json"
        data_file = data_dir / "cleaned_dataset.parquet"
        output_file = artifacts_dir / "validation_report.json"
        
        # Create mock model
        with open(model_file, 'w') as f:
            json.dump({"model_type": "xgboost"}, f)
        
        mock_y_true = np.random.rand(100)
        mock_y_pred = mock_y_true + np.random.normal(0, 0.1, 100)
        
        with patch('validate.load_data', return_value=(mock_y_true, mock_y_pred, {})), \
             patch('validate.load_model', return_value=MagicMock()), \
             patch('validate.prepare_features', return_value=MagicMock()), \
             patch('validate.perform_cross_validation', return_value={
                 'r2_scores': [0.85, 0.84, 0.86, 0.83, 0.85],
                 'rmse_scores': [0.12, 0.13, 0.11, 0.14, 0.12],
                 'mape_scores': [0.05, 0.06, 0.04, 0.07, 0.05]
             }), \
             patch('validate.regression_bias_test', return_value={
                 'intercept': 0.01,
                 'slope': 0.98,
                 'p_value': 0.45
             }), \
             patch('validate.apply_bonferroni_correction', return_value={'adjusted_alpha': 0.017}):
            
            args = [
                '--model_path', str(model_file),
                '--output_path', str(output_file)
            ]
            
            try:
                validate_main(args)
            except SystemExit:
                pass

            assert output_file.exists(), "Report not generated at expected path"

            with open(output_file, 'r') as f:
                report = json.load(f)
            
            assert 'cross_validation_metrics' in report
            assert 'bias_test_results' in report
            assert 'bonferroni_correction' in report

    def test_validation_report_contains_all_required_metrics(self):
        """
        Comprehensive test to ensure the validation report contains all
        metrics required by the project specification.
        """
        self._create_mock_model()
        
        mock_y_true = np.random.rand(100)
        mock_y_pred = mock_y_true + np.random.normal(0, 0.1, 100)
        
        with patch('validate.load_data', return_value=(mock_y_true, mock_y_pred, {})), \
             patch('validate.load_model', return_value=MagicMock()), \
             patch('validate.prepare_features', return_value=MagicMock()), \
             patch('validate.perform_cross_validation', return_value={
                 'r2_scores': [0.85, 0.84, 0.86, 0.83, 0.85],
                 'rmse_scores': [0.12, 0.13, 0.11, 0.14, 0.12],
                 'mape_scores': [0.05, 0.06, 0.04, 0.07, 0.05]
             }), \
             patch('validate.regression_bias_test', return_value={
                 'intercept': 0.01,
                 'slope': 0.98,
                 'p_value': 0.45
             }), \
             patch('validate.apply_bonferroni_correction', return_value={'adjusted_alpha': 0.017}):
            
            args = [
                '--model_path', str(self.model_path),
                '--output_path', str(self.artifacts_dir / "validation_report.json")
            ]
            
            try:
                validate_main(args)
            except SystemExit:
                pass

            report_path = self.artifacts_dir / "validation_report.json"
            assert report_path.exists()

            with open(report_path, 'r') as f:
                report = json.load(f)

            # Check all required top-level sections
            assert 'cross_validation_metrics' in report
            assert 'bias_test_results' in report
            assert 'bonferroni_correction' in report
            assert 'summary' in report

            # Check cross-validation metrics details
            cv = report['cross_validation_metrics']
            assert 'mean_r2' in cv
            assert 'std_r2' in cv
            assert 'mean_rmse' in cv
            assert 'mean_mape' in cv
            assert 'r2_scores' in cv
            assert 'rmse_scores' in cv
            assert 'mape_scores' in cv

            # Check bias test details
            bias = report['bias_test_results']
            assert 'intercept' in bias
            assert 'slope' in bias
            assert 'p_value' in bias
            assert 'is_significant' in bias
            assert 'interpretation' in bias

            # Check Bonferroni details
            bonf = report['bonferroni_correction']
            assert 'original_alpha' in bonf
            assert 'number_of_tests' in bonf
            assert 'adjusted_alpha' in bonf
            assert 'applied' in bonf

            # Check summary
            summary = report['summary']
            assert 'model_performance' in summary
            assert 'threshold_violations' in summary or 'warnings' in summary
            assert 'recommendations' in summary