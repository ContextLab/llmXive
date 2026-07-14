import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from src.reports.generate_plots import (
    create_predicted_vs_actual_scatter,
    create_residuals_histogram,
    generate_predicted_vs_actual_report
)

class TestGeneratePlots:
    @pytest.fixture
    def mock_dataframe(self):
        """Create a mock dataframe with predicted and actual outcomes."""
        np.random.seed(42)
        n = 100
        actual = np.random.choice([0.0, 0.5, 1.0], n)
        # Add some noise to predictions
        predicted = actual + np.random.normal(0, 0.1, n)
        return pd.DataFrame({
            'actual_outcome': actual,
            'predicted_outcome': predicted,
            'residuals': predicted - actual
        })

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_create_predicted_vs_actual_scatter(self, mock_dataframe, temp_dir):
        """Test that the scatter plot function creates a valid file."""
        output_path = temp_dir / "scatter_test.png"
        result_path = create_predicted_vs_actual_scatter(
            mock_dataframe,
            output_path,
            predicted_col='predicted_outcome',
            actual_col='actual_outcome'
        )

        assert Path(result_path).exists()
        assert result_path == str(output_path)
        assert output_path.stat().st_size > 0

    def test_create_residuals_histogram(self, mock_dataframe, temp_dir):
        """Test that the residuals histogram function creates a valid file."""
        output_path = temp_dir / "residuals_test.png"
        result_path = create_residuals_histogram(
            mock_dataframe,
            output_path,
            residual_col='residuals'
        )

        assert Path(result_path).exists()
        assert result_path == str(output_path)
        assert output_path.stat().st_size > 0

    def test_generate_predicted_vs_actual_report(self, mock_dataframe, temp_dir):
        """Test the full report generation pipeline."""
        # Save mock data to parquet
        parquet_path = temp_dir / "games.parquet"
        mock_dataframe.to_parquet(parquet_path)

        results_dir = temp_dir / "results"
        
        artifacts = generate_predicted_vs_actual_report(
            processed_data_path=str(parquet_path),
            output_dir=str(results_dir),
            predicted_col='predicted_outcome',
            actual_col='actual_outcome'
        )

        assert 'scatter_plot' in artifacts
        assert 'residuals_plot' in artifacts
        assert Path(artifacts['scatter_plot']).exists()
        assert Path(artifacts['residuals_plot']).exists()

    def test_missing_columns_raises_error(self, temp_dir):
        """Test that missing required columns raise a ValueError."""
        df = pd.DataFrame({'wrong_col': [1, 2, 3]})
        parquet_path = temp_dir / "bad_games.parquet"
        df.to_parquet(parquet_path)

        with pytest.raises(ValueError, match="Missing required columns"):
            generate_predicted_vs_actual_report(
                processed_data_path=str(parquet_path),
                output_dir=str(temp_dir / "results"),
                predicted_col='predicted_outcome',
                actual_col='actual_outcome'
            )

    def test_nan_handling(self, temp_dir):
        """Test that NaN values are handled gracefully."""
        df = pd.DataFrame({
            'actual_outcome': [1.0, np.nan, 0.0],
            'predicted_outcome': [0.9, 0.5, np.nan]
        })
        parquet_path = temp_dir / "nan_games.parquet"
        df.to_parquet(parquet_path)

        # Should not raise, should drop NaNs
        artifacts = generate_predicted_vs_actual_report(
            processed_data_path=str(parquet_path),
            output_dir=str(temp_dir / "results"),
            predicted_col='predicted_outcome',
            actual_col='actual_outcome'
        )
        
        assert Path(artifacts['scatter_plot']).exists()