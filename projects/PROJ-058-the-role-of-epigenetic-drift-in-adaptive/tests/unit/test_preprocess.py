import pytest
import pandas as pd
import numpy as np
import json
import tempfile
import os
from pathlib import Path
import sys

# Ensure code directory is in path for imports
code_root = Path(__file__).parent.parent.parent / 'code'
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from preprocess.rna_seq import logo_jackknife_variance, load_rna_seq_data, median_of_ratios_normalization
from preprocess.methyl import logo_jackknife_variance as methyl_logo_jackknife_variance


class TestLOGOJackknife:
    """
    Tests for the Leave-One-Generation-Out (LOGO) jackknife logic.
    Validates that the split logic correctly excludes one generation at a time
    and calculates variance on the remaining samples.
    """

    def setup_method(self):
        """
        Create synthetic small datasets for testing.
        """
        # Create synthetic RNA-seq count data
        # 5 genes, 9 samples (3 generations: G1, G2, G3, each with 3 samples)
        np.random.seed(42)
        genes = ['GeneA', 'GeneB', 'GeneC', 'GeneD', 'GeneE']
        samples = [f'S{i}' for i in range(1, 10)]
        
        # Generate deterministic data to ensure test stability
        # Using a fixed seed and simple arithmetic to avoid random variance issues
        data = np.random.randint(10, 100, size=(5, 9))
        
        self.rna_df = pd.DataFrame(data, index=genes, columns=samples)
        
        # Metadata mapping sample IDs to generations
        self.metadata = [
            {'sample_id': 'S1', 'generation': 1},
            {'sample_id': 'S2', 'generation': 1},
            {'sample_id': 'S3', 'generation': 1},
            {'sample_id': 'S4', 'generation': 2},
            {'sample_id': 'S5', 'generation': 2},
            {'sample_id': 'S6', 'generation': 2},
            {'sample_id': 'S7', 'generation': 3},
            {'sample_id': 'S8', 'generation': 3},
            {'sample_id': 'S9', 'generation': 3},
        ]

    def test_logo_jackknife_rna_shape(self):
        """Test that LOGO returns correct shape for RNA-seq data."""
        result = logo_jackknife_variance(self.rna_df, self.metadata)
        
        # Should have 5 genes (rows) and 3 generations (columns)
        assert result.shape == (5, 3), f"Expected shape (5, 3), got {result.shape}"
        expected_cols = ['loo_gen_1', 'loo_gen_2', 'loo_gen_3']
        assert list(result.columns) == expected_cols, f"Expected columns {expected_cols}, got {list(result.columns)}"

    def test_logo_jackknife_rna_values(self):
        """Test that LOGO variance is calculated correctly (non-NaN, positive)."""
        result = logo_jackknife_variance(self.rna_df, self.metadata)
        
        # Check for NaNs
        assert not result.isnull().any().any(), "LOGO result contains NaN values"
        
        # Check that values are positive (variance)
        assert (result >= 0).all().all(), "LOGO variance values should be non-negative"

    def test_logo_jackknife_single_generation(self):
        """Test behavior when only one generation exists."""
        single_gen_meta = [
            {'sample_id': 'S1', 'generation': 1},
            {'sample_id': 'S2', 'generation': 1},
            {'sample_id': 'S3', 'generation': 1},
        ]
        result = logo_jackknife_variance(self.rna_df, single_gen_meta)
        
        # With only one generation, we cannot leave one out and have samples left.
        # The expected behavior is to return NaN or handle gracefully.
        # Based on standard LOGO implementation: if N_gen=1, variance is undefined.
        assert result.shape == (5, 1), f"Expected shape (5, 1) for single gen, got {result.shape}"
        # All values should be NaN because there are no remaining samples to calculate variance from
        assert result.isnull().all().all(), "Expected NaN values for single generation LOGO as no samples remain"

    def test_logo_jackknife_methyl_shape(self):
        """Test LOGO logic for methylation data (same logic as RNA)."""
        # Reuse RNA data as proxy for methyl data structure
        result = methyl_logo_jackknife_variance(self.rna_df, self.metadata)
        
        assert result.shape == (5, 3), f"Expected shape (5, 3), got {result.shape}"
        expected_cols = ['loo_gen_1', 'loo_gen_2', 'loo_gen_3']
        assert list(result.columns) == expected_cols, f"Expected columns {expected_cols}, got {list(result.columns)}"

    def test_logo_jackknife_deterministic(self):
        """Test that LOGO produces consistent results on same input."""
        result1 = logo_jackknife_variance(self.rna_df, self.metadata)
        result2 = logo_jackknife_variance(self.rna_df, self.metadata)
        
        pd.testing.assert_frame_equal(result1, result2)

    def test_logo_jackknife_missing_samples(self):
        """Test behavior when some samples in metadata are not in data."""
        bad_metadata = [
            {'sample_id': 'S1', 'generation': 1},
            {'sample_id': 'S2', 'generation': 1},
            {'sample_id': 'S3', 'generation': 1},
            {'sample_id': 'S4', 'generation': 2},
            {'sample_id': 'S5', 'generation': 2},
            {'sample_id': 'S6', 'generation': 2},
            {'sample_id': 'S7', 'generation': 3},
            {'sample_id': 'S8', 'generation': 3},
            {'sample_id': 'S9', 'generation': 3},
            {'sample_id': 'S99', 'generation': 4}, # Not in data
        ]
        # This should still work, just ignoring S99
        result = logo_jackknife_variance(self.rna_df, bad_metadata)
        # Should have 3 generations (1, 2, 3) because 4 has no samples in data
        assert result.shape[1] == 3, "Should ignore generation with no samples"
        assert list(result.columns) == ['loo_gen_1', 'loo_gen_2', 'loo_gen_3']

    def test_logo_jackknife_variance_calculation_logic(self):
        """
        Verify that the variance is actually calculated on the remaining samples.
        We manually calculate variance for one gene and one generation exclusion
        to ensure the logic is correct.
        """
        # Use a simple dataset where we can calculate manually
        genes = ['G1']
        samples = ['S1', 'S2', 'S3'] # 1 sample per generation
        data = np.array([[10, 20, 30]])
        simple_df = pd.DataFrame(data, index=genes, columns=samples)
        simple_meta = [
            {'sample_id': 'S1', 'generation': 1},
            {'sample_id': 'S2', 'generation': 2},
            {'sample_id': 'S3', 'generation': 3},
        ]
        
        result = logo_jackknife_variance(simple_df, simple_meta)
        
        # When leaving out generation 1 (S1), we have S2 (20) and S3 (30).
        # Variance of [20, 30] is ((20-25)^2 + (30-25)^2) / (2-1) = 50.0
        # Note: pandas var() uses ddof=1 by default (sample variance)
        expected_var_gen1 = np.var([20, 30], ddof=1)
        
        # When leaving out generation 2 (S2), we have S1 (10) and S3 (30).
        # Variance of [10, 30] is 200.0
        expected_var_gen2 = np.var([10, 30], ddof=1)
        
        # When leaving out generation 3 (S3), we have S1 (10) and S2 (20).
        # Variance of [10, 20] is 50.0
        expected_var_gen3 = np.var([10, 20], ddof=1)
        
        assert abs(result.loc['G1', 'loo_gen_1'] - expected_var_gen1) < 1e-6
        assert abs(result.loc['G1', 'loo_gen_2'] - expected_var_gen2) < 1e-6
        assert abs(result.loc['G1', 'loo_gen_3'] - expected_var_gen3) < 1e-6


class TestNormalization:
    """Tests for normalization functions."""

    def setup_method(self):
        np.random.seed(42)
        genes = ['GeneA', 'GeneB']
        samples = ['S1', 'S2', 'S3']
        # Counts with different library sizes
        data = np.array([
            [100, 200, 300],
            [50, 100, 150]
        ])
        self.counts_df = pd.DataFrame(data, index=genes, columns=samples)

    def test_median_of_ratios_normalization(self):
        """Test that median-of-ratios normalization works without error."""
        result = median_of_ratios_normalization(self.counts_df)
        
        # Result should have same shape
        assert result.shape == self.counts_df.shape
        
        # Check that values are reasonable (normalized)
        assert not result.isnull().any().any()
        
        # Check that the geometric mean is used correctly (approximate check)
        # The median of ratios method divides by the geometric mean of the row
        # and then normalizes by the median of those ratios.
        # We just check that the values are non-zero and finite.
        assert (result > 0).all().all()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])