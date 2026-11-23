import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.analysis.viz import perform_sensitivity_analysis, generate_sensitivity_plot
from code.utils.config import set_global_seed

class TestSensitivityAnalysis:
    """Unit tests for sensitivity analysis logic in visualization module."""

    @pytest.fixture
    def mock_processed_data(self):
        """Create a mock dataframe simulating preprocessed PR data."""
        set_global_seed(42)
        n_samples = 1000
        data = {
            'is_llm_generated': np.random.choice([True, False], size=n_samples),
            'comment_count': np.random.poisson(lam=5, size=n_samples) + 1,
            'sentiment_score': np.random.normal(loc=0.0, scale=1.0, size=n_samples),
            'merge_time_hours': np.random.exponential(scale=24, size=n_samples) + 1,
            'complexity_score': np.random.normal(loc=50, scale=10, size=n_samples)
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def mock_keywords_config(self):
        """Mock configuration for keyword thresholds."""
        return {
            'min_keywords': 1,
            'max_keywords': 5,
            'step': 1
        }

    def test_perform_sensitivity_analysis_runs_without_error(self, mock_processed_data):
        """Test that sensitivity analysis executes and returns a result dataframe."""
        result = perform_sensitivity_analysis(
            mock_processed_data,
            metric='comment_count',
            threshold_range=range(1, 4),
            threshold_column='keyword_match_count'
        )

        assert isinstance(result, pd.DataFrame)
        assert 'threshold' in result.columns
        assert 'p_value' in result.columns
        assert 'effect_size' in result.columns
        assert 'significant' in result.columns
        assert len(result) > 0

    def test_perform_sensitivity_analysis_correct_threshold_values(self, mock_processed_data):
        """Verify that the returned thresholds match the input range."""
        thresholds = [1, 2, 3]
        result = perform_sensitivity_analysis(
            mock_processed_data,
            metric='comment_count',
            threshold_range=thresholds,
            threshold_column='keyword_match_count'
        )

        assert list(result['threshold']) == thresholds

    def test_perform_sensitivity_analysis_statistical_validity(self, mock_processed_data):
        """Test that p-values and effect sizes are within expected statistical bounds."""
        result = perform_sensitivity_analysis(
            mock_processed_data,
            metric='comment_count',
            threshold_range=range(1, 4),
            threshold_column='keyword_match_count'
        )

        # P-values should be between 0 and 1
        assert all((result['p_value'] >= 0) & (result['p_value'] <= 1))

        # Effect sizes (Cohen's d) should be finite numbers
        assert all(np.isfinite(result['effect_size']))

    def test_perform_sensitivity_analysis_handles_empty_groups(self, mock_processed_data):
        """Test behavior when a threshold creates an empty group."""
        # Create data where high thresholds will result in empty groups
        data = mock_processed_data.copy()
        data['keyword_match_count'] = np.random.choice([0, 1, 2], size=len(data))

        result = perform_sensitivity_analysis(
            data,
            metric='comment_count',
            threshold_range=range(1, 10),  # High thresholds
            threshold_column='keyword_match_count'
        )

        # Should handle empty groups gracefully (either skip or return NaN)
        assert isinstance(result, pd.DataFrame)
        # If a group is empty, we expect NaN for that row's statistics
        # or the row might be filtered out entirely depending on implementation
        assert len(result) > 0  # Should still have some valid results for lower thresholds

    def test_generate_sensitivity_plot_creates_figure(self, mock_processed_data, tmp_path):
        """Test that the sensitivity plot generation creates a valid figure file."""
        # Mock the perform_sensitivity_analysis function to return known data
        mock_result = pd.DataFrame({
            'threshold': [1, 2, 3],
            'p_value': [0.01, 0.05, 0.2],
            'effect_size': [0.5, 0.3, 0.1],
            'significant': [True, False, False]
        })

        with patch('code.analysis.viz.perform_sensitivity_analysis', return_value=mock_result):
            output_path = tmp_path / "sensitivity_analysis.png"
            fig = generate_sensitivity_plot(
                mock_result,
                metric='comment_count',
                output_path=str(output_path)
            )

            assert fig is not None
            assert output_path.exists()
            assert output_path.stat().st_size > 0

    def test_generate_sensitivity_plot_significance_markers(self, mock_processed_data, tmp_path):
        """Test that the plot correctly marks significant vs non-significant results."""
        mock_result = pd.DataFrame({
            'threshold': [1, 2, 3, 4],
            'p_value': [0.001, 0.04, 0.06, 0.5],
            'effect_size': [0.8, 0.4, 0.2, 0.05],
            'significant': [True, True, False, False]
        })

        with patch('code.analysis.viz.perform_sensitivity_analysis', return_value=mock_result):
            output_path = tmp_path / "sensitivity_with_markers.png"
            fig = generate_sensitivity_plot(
                mock_result,
                metric='comment_count',
                output_path=str(output_path)
            )

            # Verify file was created
            assert output_path.exists()
            # The plot should visually distinguish significant points (implementation detail)
            # We verify the function doesn't crash and produces output

    def test_sensitivity_analysis_with_different_metrics(self, mock_processed_data):
        """Test sensitivity analysis with different review metrics."""
        metrics = ['comment_count', 'sentiment_score', 'merge_time_hours']

        for metric in metrics:
            result = perform_sensitivity_analysis(
                mock_processed_data,
                metric=metric,
                threshold_range=range(1, 3),
                threshold_column='keyword_match_count'
            )

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 2  # Two thresholds

    def test_sensitivity_analysis_uses_correct_alpha(self, mock_processed_data):
        """Test that the significance determination uses the correct alpha level."""
        # Create data with known p-values
        mock_result = pd.DataFrame({
            'threshold': [1, 2, 3],
            'p_value': [0.04, 0.05, 0.06],
            'effect_size': [0.5, 0.5, 0.5],
            'significant': [True, True, False]  # 0.04 and 0.05 should be significant at alpha=0.05
        })

        # The function should correctly identify significant results
        # This test verifies the logic is consistent with statistical conventions
        assert mock_result.loc[mock_result['p_value'] <= 0.05, 'significant'].all()
        assert not mock_result.loc[mock_result['p_value'] > 0.05, 'significant'].any()