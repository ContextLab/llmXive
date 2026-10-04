"""
Unit tests for the statistics module (T034).
"""

import pytest
import numpy as np
from pathlib import Path
import json
import sys
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.analysis.statistics import (
    perform_welch_ttest,
    load_residuals_with_ligand_labels,
    run_statistical_analysis
)


class TestWelchTtest:
    """Tests for the Welch's t-test implementation."""

    def test_perform_welch_ttest_basic(self):
        """Test basic functionality with simple data."""
        # Create two independent groups with known statistics
        group1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        group2 = np.array([2.0, 3.0, 4.0, 5.0, 6.0])

        result = perform_welch_ttest(group1, group2)

        assert result["status"] == "completed"
        assert result["t_statistic"] is not None
        assert result["p_value"] is not None
        assert result["degrees_of_freedom"] is not None
        assert "confidence_interval" in result
        assert len(result["confidence_interval"]) == 2
        assert "effect_size" in result

    def test_perform_welch_ttest_significant_difference(self):
        """Test detection of significant difference between groups."""
        # Groups with large mean difference
        group1 = np.array([1.0, 1.5, 2.0, 1.8, 2.2])
        group2 = np.array([10.0, 11.0, 10.5, 11.5, 10.8])

        result = perform_welch_ttest(group1, group2)

        assert result["status"] == "completed"
        assert result["is_significant"] is True
        assert result["p_value"] < 0.05

    def test_perform_welch_ttest_no_difference(self):
        """Test when there is no significant difference."""
        # Groups with similar means
        np.random.seed(42)
        group1 = np.random.normal(5.0, 1.0, 100)
        group2 = np.random.normal(5.1, 1.0, 100)

        result = perform_welch_ttest(group1, group2)

        assert result["status"] == "completed"
        # May or may not be significant due to randomness
        assert result["t_statistic"] is not None
        assert result["p_value"] is not None

    def test_perform_welch_ttest_unequal_variances(self):
        """Test handling of unequal variances (Welch's key feature)."""
        # Group with small variance
        group1 = np.array([5.0, 5.1, 4.9, 5.0, 5.05])
        # Group with large variance
        group2 = np.array([5.0, 10.0, 0.0, 7.5, 2.5])

        result = perform_welch_ttest(group1, group2)

        assert result["status"] == "completed"
        # Should handle unequal variances without error
        assert result["degrees_of_freedom"] is not None

    def test_perform_welch_ttest_empty_group(self):
        """Test handling of empty groups."""
        group1 = np.array([])
        group2 = np.array([1.0, 2.0, 3.0])

        result = perform_welch_ttest(group1, group2)

        assert result["status"] == "skipped"
        assert "reason" in result

    def test_perform_welch_ttest_single_element(self):
        """Test with single element groups (should handle gracefully)."""
        group1 = np.array([1.0])
        group2 = np.array([2.0])

        result = perform_welch_ttest(group1, group2)

        # With single elements, variance is 0, so test may be skipped or return inf df
        assert result["status"] in ["completed", "skipped"]

    def test_perform_welch_ttest_output_structure(self):
        """Verify all required fields are present in output."""
        group1 = np.array([1.0, 2.0, 3.0])
        group2 = np.array([4.0, 5.0, 6.0])

        result = perform_welch_ttest(group1, group2)

        required_fields = [
            "status", "t_statistic", "p_value", "degrees_of_freedom",
            "confidence_interval", "effect_size", "sample_sizes",
            "means", "variances", "significance_level", "is_significant"
        ]

        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

    def test_perform_welch_ttest_consistency_with_scipy(self):
        """Verify results match scipy.stats.ttest_ind with equal_var=False."""
        from scipy import stats as scipy_stats

        group1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        group2 = np.array([2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0])

        result = perform_welch_ttest(group1, group2)

        # Compare with scipy
        scipy_t, scipy_p = scipy_stats.ttest_ind(group1, group2, equal_var=False)

        assert np.isclose(result["t_statistic"], scipy_t, rtol=1e-10)
        assert np.isclose(result["p_value"], scipy_p, rtol=1e-10)


class TestLoadResiduals:
    """Tests for loading residuals with ligand labels."""

    @patch('pathlib.Path.exists')
    @patch('pandas.read_parquet')
    def test_load_residuals_success(self, mock_read_parquet, mock_exists):
        """Test successful loading of residuals."""
        mock_exists.return_value = True

        # Create mock dataframe
        mock_df = MagicMock()
        mock_df.columns = ['error_ml_dft', 'ligand_class', 'sample_id']
        mock_df.loc = MagicMock()

        # Mock the loc indexer to return arrays
        group13_data = MagicMock()
        group13_data.values = np.array([0.1, 0.2, 0.3])
        conventional_data = MagicMock()
        conventional_data.values = np.array([0.4, 0.5, 0.6])

        mock_df.loc.__getitem__ = MagicMock(side_effect=[
            (MagicMock(), group13_data),  # First call for group13
            (MagicMock(), conventional_data)  # Second call for conventional
        ])

        mock_df.__getitem__ = MagicMock(return_value=MagicMock(values=np.array(['s1', 's2', 's3'])))

        mock_read_parquet.return_value = mock_df

        with patch('src.analysis.statistics.logger'):
            errors_g13, errors_conv, sample_ids = load_residuals_with_ligand_labels()

            assert len(errors_g13) == 3
            assert len(errors_conv) == 3
            assert len(sample_ids) == 3

    @patch('pathlib.Path.exists')
    def test_load_residuals_file_not_found(self, mock_exists):
        """Test handling of missing file."""
        mock_exists.return_value = False

        with pytest.raises(FileNotFoundError):
            with patch('src.analysis.statistics.logger'):
                load_residuals_with_ligand_labels()

    @patch('pathlib.Path.exists')
    @patch('pandas.read_parquet')
    def test_load_residuals_missing_columns(self, mock_read_parquet, mock_exists):
        """Test handling of missing columns."""
        mock_exists.return_value = True

        mock_df = MagicMock()
        mock_df.columns = ['error_ml_dft']  # Missing 'ligand_class'

        mock_read_parquet.return_value = mock_df

        with pytest.raises(ValueError) as excinfo:
            with patch('src.analysis.statistics.logger'):
                load_residuals_with_ligand_labels()

        assert "Missing required columns" in str(excinfo.value)


class TestRunStatisticalAnalysis:
    """Tests for the main analysis runner."""

    @patch('src.analysis.statistics.load_residuals_with_ligand_labels')
    @patch('src.analysis.statistics.perform_welch_ttest')
    @patch('src.analysis.statistics.save_statistical_results')
    @patch('pathlib.Path.mkdir')
    def test_run_statistical_analysis_success(
        self, mock_mkdir, mock_save, mock_ttest, mock_load
    ):
        """Test successful analysis run."""
        mock_load.return_value = (
            np.array([0.1, 0.2]),
            np.array([0.3, 0.4]),
            ['s1', 's2']
        )
        mock_ttest.return_value = {
            "status": "completed",
            "t_statistic": 1.5,
            "p_value": 0.15
        }

        result = run_statistical_analysis()

        assert result["status"] == "completed"
        assert mock_load.called
        assert mock_ttest.called
        assert mock_save.called

    @patch('src.analysis.statistics.load_residuals_with_ligand_labels')
    @patch('pathlib.Path.mkdir')
    def test_run_statistical_analysis_load_failure(self, mock_mkdir, mock_load):
        """Test handling of data loading failure."""
        mock_load.side_effect = FileNotFoundError("File not found")

        result = run_statistical_analysis()

        assert result["status"] == "failed"
        assert "error" in result

    @patch('src.analysis.statistics.load_residuals_with_ligand_labels')
    @patch('src.analysis.statistics.perform_welch_ttest')
    @patch('pathlib.Path.mkdir')
    def test_run_statistical_analysis_skipped(self, mock_mkdir, mock_ttest, mock_load):
        """Test when test is skipped."""
        mock_load.return_value = (
            np.array([]),
            np.array([0.1, 0.2]),
            []
        )
        mock_ttest.return_value = {
            "status": "skipped",
            "reason": "One or both groups have zero samples"
        }

        result = run_statistical_analysis()

        assert result["status"] == "skipped"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])