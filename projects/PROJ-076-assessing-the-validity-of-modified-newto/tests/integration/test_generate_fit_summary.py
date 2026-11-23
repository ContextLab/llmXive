"""
Integration test for fit summary generation (T025).

Tests that the generate_fit_summary script produces a valid CSV with
expected columns and data types when run on real fitted data.
"""
import os
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil

from generate_fit_summary import aggregate_fit_results, main
from fit import fit_all_galaxies
from utils import get_logger


class TestFitSummaryGeneration:
    """Test suite for fit summary generation."""

    @pytest.fixture
    def sample_fit_results(self):
        """Create sample fit results for testing."""
        return [
            {
                'galaxy_name': 'NGC3198',
                'model_name': 'mond_simple',
                'metrics': {
                    'reduced_chi2': 1.23,
                    'aic': 45.6,
                    'bic': 52.1,
                    'n_parameters': 3,
                    'n_points': 45
                },
                'convergence': True,
                'message': 'Optimization converged'
            },
            {
                'galaxy_name': 'NGC3198',
                'model_name': 'nfw',
                'metrics': {
                    'reduced_chi2': 1.45,
                    'aic': 48.2,
                    'bic': 54.7,
                    'n_parameters': 3,
                    'n_points': 45
                },
                'convergence': True,
                'message': 'Optimization converged'
            },
            {
                'galaxy_name': 'UGC128',
                'model_name': 'mond_simple',
                'metrics': {
                    'reduced_chi2': 0.98,
                    'aic': 32.1,
                    'bic': 38.5,
                    'n_parameters': 3,
                    'n_points': 38
                },
                'convergence': False,
                'message': 'Maximum iterations reached'
            }
        ]

    @pytest.fixture
    def sample_galaxies_df(self):
        """Create sample galaxy metadata DataFrame."""
        return pd.DataFrame({
            'name': ['NGC3198', 'UGC128'],
            'distance': [9.0, 12.5],
            'inclination': [75.0, 82.0]
        })

    def test_aggregate_fit_results_structure(self, sample_fit_results, sample_galaxies_df):
        """Test that aggregate_fit_results produces correct DataFrame structure."""
        result_df = aggregate_fit_results(sample_fit_results, sample_galaxies_df)

        expected_columns = [
            'galaxy', 'model', 'reduced_chi2', 'aic', 'bic',
            'n_parameters', 'n_points', 'convergence', 'message'
        ]

        assert list(result_df.columns) == expected_columns
        assert len(result_df) == 3  # 3 fit results

    def test_aggregate_fit_results_data_types(self, sample_fit_results, sample_galaxies_df):
        """Test that aggregated data has correct types."""
        result_df = aggregate_fit_results(sample_fit_results, sample_galaxies_df)

        assert result_df['galaxy'].dtype == 'object'
        assert result_df['model'].dtype == 'object'
        assert pd.api.types.is_float_dtype(result_df['reduced_chi2'])
        assert pd.api.types.is_float_dtype(result_df['aic'])
        assert pd.api.types.is_float_dtype(result_df['bic'])
        assert pd.api.types.is_integer_dtype(result_df['n_parameters'])
        assert pd.api.types.is_integer_dtype(result_df['n_points'])
        assert pd.api.types.is_bool_dtype(result_df['convergence'])

    def test_aggregate_fit_results_values(self, sample_fit_results, sample_galaxies_df):
        """Test that aggregated data contains correct values."""
        result_df = aggregate_fit_results(sample_fit_results, sample_galaxies_df)

        # Check specific values
        mond_row = result_df[(result_df['galaxy'] == 'NGC3198') &
                             (result_df['model'] == 'mond_simple')]
        assert len(mond_row) == 1
        assert mond_row['reduced_chi2'].values[0] == 1.23
        assert mond_row['aic'].values[0] == 45.6
        assert mond_row['convergence'].values[0] is True

        # Check non-converged case
        non_conv_row = result_df[(result_df['galaxy'] == 'UGC128') &
                                 (result_df['model'] == 'mond_simple')]
        assert len(non_conv_row) == 1
        assert non_conv_row['convergence'].values[0] is False

    def test_main_creates_csv_file(self, sample_fit_results, sample_galaxies_df, tmp_path):
        """Test that main() creates the output CSV file."""
        # Create temporary directories
        data_dir = tmp_path / 'data' / 'processed'
        results_dir = tmp_path / 'results'
        data_dir.mkdir(parents=True)

        # Create a minimal filtered_galaxies.csv
        filtered_file = data_dir / 'filtered_galaxies.csv'
        sample_galaxies_df.to_csv(filtered_file, index=False)

        # Mock fit_all_galaxies to return our sample results
        original_fit_all = fit_all_galaxies
        def mock_fit_all(df, config):
            return sample_fit_results

        import generate_fit_summary
        generate_fit_summary.fit_all_galaxies = mock_fit_all

        # Patch config paths
        original_load_config = generate_fit_summary.load_config
        def mock_load_config():
            return {
                'data_dir': str(tmp_path / 'data'),
                'output_dir': str(results_dir)
            }
        generate_fit_summary.load_config = mock_load_config

        # Run main
        output_file = main()

        # Verify output
        assert output_file.exists()
        assert output_file.name == 'fit_summary.csv'

        # Load and verify contents
        df = pd.read_csv(output_file)
        assert len(df) == 3
        assert 'reduced_chi2' in df.columns
        assert 'aic' in df.columns
        assert 'bic' in df.columns

        # Restore mocks
        generate_fit_summary.fit_all_galaxies = original_fit_all
        generate_fit_summary.load_config = original_load_config

    def test_main_handles_missing_data(self, tmp_path):
        """Test that main() handles missing filtered data gracefully."""
        data_dir = tmp_path / 'data' / 'processed'
        results_dir = tmp_path / 'results'
        data_dir.mkdir(parents=True)

        # No filtered_galaxies.csv exists

        import generate_fit_summary
        original_load_config = generate_fit_summary.load_config
        def mock_load_config():
            return {
                'data_dir': str(tmp_path / 'data'),
                'output_dir': str(results_dir)
            }
        generate_fit_summary.load_config = mock_load_config

        # Run main - should return None and log error
        output = main()

        assert output is None

        # Restore
        generate_fit_summary.load_config = original_load_config