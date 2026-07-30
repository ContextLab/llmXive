import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

from src.reports.generate_plots import (
    generate_diagnostic_report,
    create_predicted_vs_actual_plot,
    create_residual_plot,
    create_feature_importance_plot
)

class TestGenerateDiagnostics:
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_generate_diagnostic_report_creates_file(self, temp_dir):
        """Test that generate_diagnostic_report creates a valid JSON file."""
        model_metrics = {
            "models": {
                "Gaussian GLM": {"r_squared": 0.85, "aic": 1234.5}
            }
        }
        residuals_stats = {
            "GLM": {"mean": 0.01, "std": 0.1}
        }
        plots_info = {
            "residuals_GLM": "data/results/residuals_GLM.png"
        }
        output_path = temp_dir / "diagnostics.json"

        result = generate_diagnostic_report(
            model_metrics, residuals_stats, plots_info, output_path
        )

        assert output_path.exists()
        assert result["summary"]["total_models_evaluated"] == 1
        assert result["summary"]["total_plots_created"] == 1

    def test_create_predicted_vs_actual_plot_creates_file(self, temp_dir):
        """Test that create_predicted_vs_actual_plot saves a PNG file."""
        df = pd.DataFrame({
            'outcome': [0, 1, 0.5],
            'predicted_outcome_Test': [0.1, 0.9, 0.4]
        })
        output_path = temp_dir / "test_plot.png"

        create_predicted_vs_actual_plot(df, 'predicted_outcome_Test', output_path)

        assert output_path.exists()
        assert output_path.suffix == '.png'

    def test_create_residual_plot_creates_file(self, temp_dir):
        """Test that create_residual_plot saves a PNG file."""
        residuals = pd.Series([0.1, -0.2, 0.05])
        output_path = temp_dir / "residual_plot.png"

        create_residual_plot(residuals, output_path)

        assert output_path.exists()
        assert output_path.suffix == '.png'

    def test_create_feature_importance_plot_creates_file(self, temp_dir):
        """Test that create_feature_importance_plot saves a PNG file."""
        coefficients = {
            'feature_A': 0.5,
            'feature_B': -0.3,
            'feature_C': 0.1
        }
        output_path = temp_dir / "importance_plot.png"

        create_feature_importance_plot(coefficients, output_path)

        assert output_path.exists()
        assert output_path.suffix == '.png'

    def test_generate_diagnostic_report_includes_summary(self, temp_dir):
        """Test that the diagnostic report includes a summary section."""
        model_metrics = {"models": {"GLM": {}}}
        residuals_stats = {"GLM": {"mean": 0.0, "std": 0.1}}
        plots_info = {"plot1": "path/to/plot.png"}
        output_path = temp_dir / "diagnostics.json"

        result = generate_diagnostic_report(model_metrics, residuals_stats, plots_info, output_path)

        assert "summary" in result
        assert "total_models_evaluated" in result["summary"]
        assert "total_plots_created" in result["summary"]
        assert "residuals_mean_all" in result["summary"]
        assert "residuals_std_all" in result["summary"]