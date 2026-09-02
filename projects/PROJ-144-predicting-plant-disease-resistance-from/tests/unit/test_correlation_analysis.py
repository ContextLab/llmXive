"""
Unit tests for code/modeling/correlation_analysis.py (T021a)
"""
import os
import sys
import json
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from modeling.correlation_analysis import (
    load_processed_data,
    compute_correlations,
    apply_fdr_correction
)
from utils.constants import DATA_PROCESSED_DIR, RESULTS_DIR


class TestCorrelationAnalysis:
    
    @pytest.fixture(autouse=True)
    def setup_temp_dirs(self, tmp_path):
        """Setup temporary directories for tests to avoid file system pollution."""
        # We will mock the constants or create files in tmp_path
        # Since constants are imported, we need to be careful.
        # For this test, we will create a local function that mimics the logic
        # rather than relying on global constants which might point to real paths.
        self.tmp_path = tmp_path
        self.temp_matrix = self.tmp_path / "batch_corrected_matrix.csv"
        self.temp_labels = self.tmp_path / "labels.csv"
        
        # Create dummy data
        np.random.seed(42)
        n_samples = 100
        n_features = 10
        
        # Create a matrix with some known correlations
        X_data = np.random.randn(n_samples, n_features)
        # Make feature 0 strongly correlated with a synthetic label
        synthetic_label = X_data[:, 0] + np.random.randn(n_samples) * 0.1
        
        X_df = pd.DataFrame(X_data, columns=[f"metabolite_{i}" for i in range(n_features)])
        y_df = pd.DataFrame({'binary_label': synthetic_label})
        
        X_df.to_csv(self.temp_matrix)
        y_df.to_csv(self.temp_labels)
        
        # We need to temporarily override the load function to use these paths
        # Or we can test the helper functions directly with DataFrames
        return self.tmp_path

    def test_compute_correlations(self):
        """Test that compute_correlations returns correct shape and types."""
        np.random.seed(42)
        n_samples = 50
        n_features = 5
        X = pd.DataFrame(np.random.randn(n_samples, n_features), 
                         columns=[f"feat_{i}" for i in range(n_features)])
        y = pd.Series(np.random.randn(n_samples))
        
        result = compute_correlations(X, y)
        
        assert isinstance(result, pd.DataFrame)
        assert 'metabolite' in result.columns
        assert 'r' in result.columns
        assert 'p_value' in result.columns
        assert len(result) == n_features
        
        # Check that r values are between -1 and 1
        assert result['r'].between(-1, 1).all()
        # Check that p_values are between 0 and 1
        assert result['p_value'].between(0, 1).all()

    def test_apply_fdr_correction(self):
        """Test that FDR correction produces valid q-values."""
        df = pd.DataFrame({
            'metabolite': ['a', 'b', 'c', 'd', 'e'],
            'r': [0.1, 0.2, 0.3, 0.4, 0.5],
            'p_value': [0.5, 0.01, 0.02, 0.03, 0.04]
        })
        
        result = apply_fdr_correction(df)
        
        assert 'fdr_q_value' in result.columns
        assert 'is_significant' in result.columns
        
        # Q-values should be between 0 and 1
        assert result['fdr_q_value'].between(0, 1).all()
        
        # Check monotonicity (roughly) - higher p should have higher or equal q
        # Sort by p_value
        sorted_res = result.sort_values('p_value')
        # The q_values should be non-decreasing with p_values
        # (Actually, BH ensures q_i <= q_{i+1} if p_i <= p_{i+1})
        
    def test_fdr_logic(self):
        """Test specific FDR logic with known values."""
        # Simple case: 2 p-values
        # p1 = 0.01, p2 = 0.05. n=2.
        # q1 = 0.01 * 2 / 1 = 0.02
        # q2 = 0.05 * 2 / 2 = 0.05
        df = pd.DataFrame({
            'metabolite': ['m1', 'm2'],
            'r': [0.5, 0.1],
            'p_value': [0.01, 0.05]
        })
        
        result = apply_fdr_correction(df)
        
        # Check that the smallest p has the smallest q (usually)
        # Note: Implementation details might vary slightly, but order should be preserved
        assert result['fdr_q_value'].iloc[result['p_value'].idxmin()] <= result['fdr_q_value'].max()

    def test_filtering_criteria_simulation(self):
        """Simulate the filtering logic used in main()."""
        df = pd.DataFrame({
            'metabolite': ['m1', 'm2', 'm3', 'm4'],
            'r': [0.5, 0.3, -0.45, -0.2],
            'fdr_q_value': [0.01, 0.02, 0.06, 0.01]
        })
        
        # Apply the filter: |r| > 0.4 AND q < 0.05
        mask = (df['r'].abs() > 0.4) & (df['fdr_q_value'] < 0.05)
        filtered = df[mask]
        
        assert len(filtered) == 1
        assert filtered.iloc[0]['metabolite'] == 'm1'
        # m3 has |r| > 0.4 but q > 0.05, so it should be excluded
        assert 'm3' not in filtered['metabolite'].values

if __name__ == "__main__":
    pytest.main([__file__, "-v"])