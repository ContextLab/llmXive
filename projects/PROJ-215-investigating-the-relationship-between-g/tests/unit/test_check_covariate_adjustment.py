import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from code.check_covariate_adjustment import calculate_max_delta_pvals

class TestCalculateMaxDeltaPvals:
    """Unit tests for the calculate_max_delta_pvals function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create sample unadjusted p-values data
        self.unadj_data = pd.DataFrame({
            'taxon': ['Taxon_A', 'Taxon_B', 'Taxon_C', 'Taxon_D'],
            'pval_unadj': [0.01, 0.05, 0.10, 0.50]
        })
        
        # Create sample adjusted p-values data (q-values)
        self.adj_data = pd.DataFrame({
            'taxon': ['Taxon_A', 'Taxon_B', 'Taxon_C', 'Taxon_D'],
            'pval_adj': [0.02, 0.15, 0.20, 0.60]
        })
        
        # Write to temp files
        self.unadj_path = os.path.join(self.temp_dir, 'unadjusted_taxa_pvals.csv')
        self.adj_path = os.path.join(self.temp_dir, 'adjusted_taxa_pvals.csv')
        
        self.unadj_data.to_csv(self.unadj_path, index=False)
        self.adj_data.to_csv(self.adj_path, index=False)

    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_calculate_max_delta(self):
        """Test that max delta is calculated correctly."""
        max_delta = calculate_max_delta_pvals(self.unadj_path, self.adj_path)
        
        # Expected deltas: |0.02-0.01|=0.01, |0.15-0.05|=0.10, |0.20-0.10|=0.10, |0.60-0.50|=0.10
        # Max should be 0.10
        expected_max = 0.10
        assert abs(max_delta - expected_max) < 1e-6, f"Expected {expected_max}, got {max_delta}"

    def test_different_deltas(self):
        """Test with varying delta values."""
        # Create data with a clear maximum delta
        unadj_data = pd.DataFrame({
            'taxon': ['Taxon_X', 'Taxon_Y'],
            'pval_unadj': [0.01, 0.02]
        })
        adj_data = pd.DataFrame({
            'taxon': ['Taxon_X', 'Taxon_Y'],
            'pval_adj': [0.50, 0.03]
        })
        
        unadj_path = os.path.join(self.temp_dir, 'test_unadj.csv')
        adj_path = os.path.join(self.temp_dir, 'test_adj.csv')
        
        unadj_data.to_csv(unadj_path, index=False)
        adj_data.to_csv(adj_path, index=False)
        
        max_delta = calculate_max_delta_pvals(unadj_path, adj_path)
        
        # Expected: |0.50-0.01|=0.49, |0.03-0.02|=0.01 -> Max is 0.49
        assert abs(max_delta - 0.49) < 1e-6, f"Expected 0.49, got {max_delta}"

    def test_missing_taxon_in_one_file(self):
        """Test handling of missing taxa in one of the files."""
        unadj_data = pd.DataFrame({
            'taxon': ['Taxon_A', 'Taxon_B', 'Taxon_C'],
            'pval_unadj': [0.01, 0.05, 0.10]
        })
        adj_data = pd.DataFrame({
            'taxon': ['Taxon_A', 'Taxon_C'],  # Taxon_B missing
            'pval_adj': [0.02, 0.20]
        })
        
        unadj_path = os.path.join(self.temp_dir, 'unadj_missing.csv')
        adj_path = os.path.join(self.temp_dir, 'adj_missing.csv')
        
        unadj_data.to_csv(unadj_path, index=False)
        adj_data.to_csv(adj_path, index=False)
        
        # Should only calculate for common taxa (Taxon_A and Taxon_C)
        max_delta = calculate_max_delta_pvals(unadj_path, adj_path)
        
        # Expected: |0.02-0.01|=0.01, |0.20-0.10|=0.10 -> Max is 0.10
        assert abs(max_delta - 0.10) < 1e-6, f"Expected 0.10, got {max_delta}"

    def test_no_common_taxa(self):
        """Test error handling when no common taxa exist."""
        unadj_data = pd.DataFrame({
            'taxon': ['Taxon_A', 'Taxon_B'],
            'pval_unadj': [0.01, 0.05]
        })
        adj_data = pd.DataFrame({
            'taxon': ['Taxon_C', 'Taxon_D'],  # No overlap
            'pval_adj': [0.02, 0.06]
        })
        
        unadj_path = os.path.join(self.temp_dir, 'unadj_no_overlap.csv')
        adj_path = os.path.join(self.temp_dir, 'adj_no_overlap.csv')
        
        unadj_data.to_csv(unadj_path, index=False)
        adj_data.to_csv(adj_path, index=False)
        
        with pytest.raises(ValueError, match="Could not find common taxon identifier"):
            calculate_max_delta_pvals(unadj_path, adj_path)

    def test_numeric_coercion(self):
        """Test handling of non-numeric values."""
        unadj_data = pd.DataFrame({
            'taxon': ['Taxon_A', 'Taxon_B'],
            'pval_unadj': [0.01, 'invalid']
        })
        adj_data = pd.DataFrame({
            'taxon': ['Taxon_A', 'Taxon_B'],
            'pval_adj': [0.02, 0.06]
        })
        
        unadj_path = os.path.join(self.temp_dir, 'unadj_invalid.csv')
        adj_path = os.path.join(self.temp_dir, 'adj_invalid.csv')
        
        unadj_data.to_csv(unadj_path, index=False)
        adj_data.to_csv(adj_path, index=False)
        
        # Should handle invalid values by coercing to NaN and ignoring them
        max_delta = calculate_max_delta_pvals(unadj_path, adj_path)
        
        # Only Taxon_A should contribute: |0.02-0.01|=0.01
        assert abs(max_delta - 0.01) < 1e-6, f"Expected 0.01, got {max_delta}"