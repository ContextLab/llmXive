import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.reports.generate_diagnostics import (
    load_model_metrics,
    generate_diagnostic_summary,
    run_diagnostic_pipeline
)

class TestGenerateDiagnostics:
    
    @pytest.fixture
    def mock_metrics_data(self):
        return {
            "gaussian_glm": {
                "r_squared": 0.45,
                "mse": 0.12,
                "aic": 1234.5,
                "cross_validation_std_r2": 0.02,
                "significant_predictors": ["eco_K", "time_white"],
                "fdr_corrected": True
            },
            "ridge_regression": {
                "r_squared": 0.44,
                "mse": 0.13,
                "aic": 1240.0,
                "cross_validation_std_r2": 0.03,
                "significant_predictors": ["eco_K"],
                "fdr_corrected": True
            }
        }

    @pytest.fixture
    def temp_results_dir(self, tmp_path):
        # Create a temporary directory structure mimicking data/results
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        return results_dir

    def test_generate_diagnostic_summary(self, mock_metrics_data):
        """Test that the summary is correctly aggregated from metrics."""
        plot_paths = ["plot1.png", "plot2.png"]
        
        report = generate_diagnostic_summary(mock_metrics_data, plot_paths)
        
        assert report["report_type"] == "DiagnosticReport"
        assert report["plots_included"] == plot_paths
        assert "gaussian_glm" in report["metrics_summary"]
        assert report["metrics_summary"]["gaussian_glm"]["r_squared"] == 0.45
        assert report["metrics_summary"]["gaussian_glm"]["significant_predictors_count"] == 2

    def test_run_diagnostic_pipeline_integration(self, temp_results_dir, mock_metrics_data):
        """Test the full pipeline execution with mocked dependencies."""
        # Setup mock metrics file
        metrics_path = temp_results_dir / "model_metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump(mock_metrics_data, f)
        
        # Create a fake plot file to ensure it gets picked up
        fake_plot = temp_results_dir / "residuals.png"
        fake_plot.touch()

        # Mock the config to point to our temp directory
        with patch('src.reports.generate_diagnostics.get_data_path') as mock_get_path:
            mock_get_path.return_value = str(temp_results_dir)
            
            output_path = temp_results_dir / "diagnostics.json"
            
            # Run the pipeline
            result = run_diagnostic_pipeline(str(output_path))
            
            # Verify output file exists
            assert output_path.exists()
            
            # Verify content
            with open(output_path, 'r') as f:
                saved_report = json.load(f)
            
            assert saved_report["report_type"] == "DiagnosticReport"
            assert len(saved_report["plots_included"]) == 1
            assert "residuals.png" in saved_report["plots_included"][0]
            assert saved_report["metrics_summary"]["gaussian_glm"]["r_squared"] == 0.45

    def test_pipeline_handles_missing_metrics(self, temp_results_dir):
        """Test that pipeline fails gracefully if metrics are missing."""
        with patch('src.reports.generate_diagnostics.get_data_path') as mock_get_path:
            mock_get_path.return_value = str(temp_results_dir)
            
            output_path = temp_results_dir / "diagnostics.json"
            
            with pytest.raises(FileNotFoundError):
                run_diagnostic_pipeline(str(output_path))