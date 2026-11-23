"""
Unit tests for generate_fit_summary module.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from generate_fit_summary import load_fit_results, aggregate_metrics, write_fit_summary


class TestLoadFitResults:
    def test_load_existing_csv(self, tmp_path):
        """Test loading existing fit results CSV."""
        results_file = tmp_path / "fit_results.csv"
        test_data = {
            'galaxy_id': ['NGC123', 'NGC456'],
            'model_type': ['mond', 'nfw'],
            'reduced_chi2': [1.2, 1.5],
            'aic': [100.5, 105.2],
            'bic': [102.1, 107.8],
            'n_params': [3, 4],
            'n_points': [25, 30],
            'fit_status': ['success', 'success']
        }
        pd.DataFrame(test_data).to_csv(results_file, index=False)
        
        results = load_fit_results(tmp_path)
        
        assert len(results) == 2
        assert results[0]['galaxy_id'] == 'NGC123'
        assert results[1]['model_type'] == 'nfw'
        assert results[0]['reduced_chi2'] == 1.2

    def test_missing_file_triggers_error(self, tmp_path):
        """Test that missing file raises appropriate error."""
        # Don't create the file
        with pytest.raises(FileNotFoundError):
            load_fit_results(tmp_path)


class TestAggregateMetrics:
    def test_aggregate_basic(self):
        """Test basic aggregation of fit metrics."""
        fit_results = [
            {
                'galaxy_id': 'NGC123',
                'model_type': 'mond',
                'reduced_chi2': 1.2,
                'aic': 100.5,
                'bic': 102.1,
                'n_params': 3,
                'n_points': 25,
                'fit_status': 'success'
            },
            {
                'galaxy_id': 'NGC123',
                'model_type': 'nfw',
                'reduced_chi2': 1.5,
                'aic': 105.2,
                'bic': 107.8,
                'n_params': 4,
                'n_points': 25,
                'fit_status': 'success'
            }
        ]
        
        df = aggregate_metrics(fit_results)
        
        assert len(df) == 2
        assert df['galaxy_id'].nunique() == 1
        assert set(df['model_type']) == {'mond', 'nfw'}
        assert df['reduced_chi2'].iloc[0] == 1.2
        assert df['reduced_chi2'].iloc[1] == 1.5

    def test_handles_missing_fields(self):
        """Test that missing fields are handled gracefully."""
        fit_results = [
            {
                'galaxy_id': 'NGC123',
                'model_type': 'mond',
                # Missing other fields
            }
        ]
        
        df = aggregate_metrics(fit_results)
        
        assert len(df) == 1
        assert pd.isna(df['reduced_chi2'].iloc[0])
        assert df['galaxy_id'].iloc[0] == 'NGC123'


class TestWriteFitSummary:
    def test_write_csv(self, tmp_path):
        """Test writing fit summary to CSV."""
        df_summary = pd.DataFrame({
            'galaxy_id': ['NGC123', 'NGC456'],
            'model_type': ['mond', 'nfw'],
            'reduced_chi2': [1.2, 1.5],
            'aic': [100.5, 105.2],
            'bic': [102.1, 107.8],
            'n_params': [3, 4],
            'n_points': [25, 30],
            'fit_status': ['success', 'success']
        })
        
        output_file = tmp_path / "fit_summary.csv"
        write_fit_summary(df_summary, output_file)
        
        assert output_file.exists()
        
        # Verify content
        df_loaded = pd.read_csv(output_file)
        assert len(df_loaded) == 2
        assert list(df_loaded.columns) == list(df_summary.columns)

    def test_creates_parent_directory(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        df_summary = pd.DataFrame({
            'galaxy_id': ['NGC123'],
            'model_type': ['mond'],
            'reduced_chi2': [1.2]
        })
        
        output_file = tmp_path / "subdir" / "fit_summary.csv"
        write_fit_summary(df_summary, output_file)
        
        assert output_file.exists()