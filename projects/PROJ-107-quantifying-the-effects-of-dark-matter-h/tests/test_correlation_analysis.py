import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import numpy as np

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.correlation_analysis import (
    compute_correlations,
    run_correlation_analysis,
    merge_datasets
)

class TestCorrelationAnalysis:

    @pytest.fixture
    def sample_data(self):
        """Create sample dataframes for testing."""
        # Alignment angles
        alignment = pd.DataFrame({
            'halo_id': [1, 1, 2, 2],
            'galaxy_id': [10, 11, 12, 13],
            'spin_spin_angle': [10.0, 20.0, 15.0, 25.0],
            'major_major_angle': [5.0, 15.0, 10.0, 20.0]
        })

        # Galaxy properties
        galaxy_props = pd.DataFrame({
            'halo_id': [1, 1, 2, 2],
            'galaxy_id': [10, 11, 12, 13],
            'sfr': [100.0, 120.0, 110.0, 130.0],
            'radius': [5.0, 6.0, 5.5, 6.5]
        })

        # Halo shapes
        halo_shapes = pd.DataFrame({
            'halo_id': [1, 2],
            'b_a_ratio': [0.6, 0.7],
            'c_a_ratio': [0.5, 0.6],
            'triaxiality': [0.5, 0.4],
            'mass': [1e12, 1.2e12]
        })

        return alignment, galaxy_props, halo_shapes

    def test_merge_datasets(self, sample_data):
        """Test that datasets are merged correctly."""
        alignment, galaxy_props, halo_shapes = sample_data
        merged = merge_datasets(halo_shapes, galaxy_props, alignment)

        assert len(merged) == 4
        assert 'spin_spin_angle' in merged.columns
        assert 'sfr' in merged.columns
        assert 'triaxiality' in merged.columns
        assert 'galaxy_id' in merged.columns

    def test_compute_correlations_basic(self, sample_data):
        """Test basic correlation computation."""
        alignment, galaxy_props, halo_shapes = sample_data
        merged = merge_datasets(halo_shapes, galaxy_props, alignment)

        result = compute_correlations(merged, 'spin_spin_angle', 'sfr')

        assert result['predictor'] == 'spin_spin_angle'
        assert result['outcome'] == 'sfr'
        assert result['n'] == 4
        assert 'correlation' in result
        assert 'p_value' in result
        assert result['status'] == 'success'

    def test_compute_correlations_nan_handling(self):
        """Test that NaN values are handled by dropping."""
        df = pd.DataFrame({
            'x': [1.0, 2.0, np.nan, 4.0],
            'y': [1.0, 2.0, 3.0, np.nan]
        })

        result = compute_correlations(df, 'x', 'y')
        # Only 2 pairs are valid (1,1) and (2,2)
        assert result['n'] == 2
        assert result['status'] == 'success'
        # Perfect correlation for 2 points
        assert np.isclose(result['correlation'], 1.0)

    def test_compute_correlations_insufficient_data(self):
        """Test behavior when too few data points."""
        df = pd.DataFrame({
            'x': [1.0],
            'y': [2.0]
        })

        result = compute_correlations(df, 'x', 'y')
        assert result['status'] == 'insufficient_data'
        assert np.isnan(result['correlation'])

    def test_run_correlation_analysis_multiple(self, sample_data):
        """Test running analysis for multiple predictor/outcome pairs."""
        alignment, galaxy_props, halo_shapes = sample_data
        merged = merge_datasets(halo_shapes, galaxy_props, alignment)

        results = run_correlation_analysis(
            merged,
            predictors=['spin_spin_angle', 'major_major_angle'],
            outcomes=['sfr', 'radius']
        )

        assert len(results) == 4 # 2 preds * 2 outcomes
        for res in results:
            assert res['status'] == 'success'

    def test_run_correlation_analysis_kendall(self, sample_data):
        """Test Kendall tau method."""
        alignment, galaxy_props, halo_shapes = sample_data
        merged = merge_datasets(halo_shapes, galaxy_props, alignment)

        results = run_correlation_analysis(
            merged,
            predictors=['spin_spin_angle'],
            outcomes=['sfr'],
            method='kendall'
        )

        assert results[0]['method'] == 'kendall'
        assert results[0]['status'] == 'success'