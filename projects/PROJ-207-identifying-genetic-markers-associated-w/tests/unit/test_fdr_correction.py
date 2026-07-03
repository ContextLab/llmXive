"""
Unit tests for Benjamini-Hochberg FDR correction implementation.
"""
import os
import sys
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.fdr_correction import calculate_q_values, apply_fdr_correction


class TestCalculateQValues:
    """Tests for the core BH q-value calculation logic."""

    def test_empty_array(self):
        """Test handling of empty input."""
        result = calculate_q_values(np.array([]))
        assert len(result) == 0
        assert isinstance(result, np.ndarray)

    def test_single_value(self):
        """Test with a single p-value."""
        p = np.array([0.05])
        q = calculate_q_values(p)
        # For n=1: q = (1/1) * 0.05 = 0.05
        assert np.isclose(q[0], 0.05)

    def test_perfectly_uniform_pvalues(self):
        """Test with p-values 0.1, 0.2, ..., 1.0."""
        p = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
        q = calculate_q_values(p)
        
        # Sorted p: same as input
        # Expected q_i = min( (10/i) * p_i, 1.0 )
        # i=1: 10 * 0.1 = 1.0
        # i=2: 5 * 0.2 = 1.0
        # ... all should be 1.0 due to monotonicity and capping
        assert np.allclose(q, 1.0)

    def test_small_pvalues(self):
        """Test with very small p-values where correction should be significant."""
        p = np.array([0.001, 0.002, 0.003, 0.004, 0.005])
        q = calculate_q_values(p)
        
        # n = 5
        # i=1 (0.001): 5 * 0.001 = 0.005
        # i=2 (0.002): 2.5 * 0.002 = 0.005
        # i=3 (0.003): 1.66 * 0.003 = 0.005
        # i=4 (0.004): 1.25 * 0.004 = 0.005
        # i=5 (0.005): 1.0 * 0.005 = 0.005
        # Monotonicity check: all 0.005
        assert np.allclose(q, 0.005)

    def test_monotonicity_enforcement(self):
        """Test that q-values are monotonically non-decreasing."""
        # Create p-values that would produce non-monotonic q-values without correction
        # e.g., p = [0.01, 0.02, 0.03, 0.04, 0.05]
        # Without monotonicity enforcement, q might dip
        p = np.array([0.01, 0.02, 0.03, 0.04, 0.05])
        q = calculate_q_values(p)
        
        # Check monotonicity: q[i] <= q[i+1] for all i
        assert np.all(np.diff(q) >= 0), "Q-values must be monotonically non-decreasing"

    def test_capping_at_one(self):
        """Test that q-values never exceed 1.0."""
        p = np.array([0.8, 0.9, 0.95, 0.99])
        q = calculate_q_values(p)
        assert np.all(q <= 1.0)

    def test_unsorted_input_preserves_order(self):
        """Test that unsorted input returns q-values in original order."""
        p = np.array([0.5, 0.1, 0.9, 0.2])
        q = calculate_q_values(p)
        
        # The q-value for 0.1 (index 1) should be the smallest
        # The q-value for 0.9 (index 2) should be the largest
        assert q[1] < q[0]
        assert q[1] < q[3]
        assert q[2] > q[0]
        assert q[2] > q[1]
        assert q[2] > q[3]


class TestApplyFdrCorrection:
    """Tests for the file-based FDR correction function."""

    def test_basic_file_processing(self):
        """Test processing a simple TSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = os.path.join(tmpdir, 'input.tsv')
            output_file = os.path.join(tmpdir, 'output.tsv')
            
            # Create test data
            df = pd.DataFrame({
                'SNP': ['rs1', 'rs2', 'rs3'],
                'P': [0.01, 0.05, 0.10]
            })
            df.to_csv(input_file, sep='\t', index=False)
            
            # Run correction
            apply_fdr_correction(input_file, output_file)
            
            # Verify output
            result = pd.read_csv(output_file, sep='\t')
            assert 'Q' in result.columns
            assert len(result) == 3
            assert result['SNP'].tolist() == ['rs1', 'rs2', 'rs3']
            
            # Verify monotonicity in output
            q_values = result['Q'].values
            assert np.all(np.diff(q_values) >= 0)

    def test_missing_input_file(self):
        """Test error handling for missing input file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, 'output.tsv')
            with pytest.raises(FileNotFoundError):
                apply_fdr_correction('nonexistent.tsv', output_file)

    def test_missing_p_column(self):
        """Test error handling when p-value column is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = os.path.join(tmpdir, 'input.tsv')
            output_file = os.path.join(tmpdir, 'output.tsv')
            
            df = pd.DataFrame({
                'SNP': ['rs1', 'rs2'],
                'PVALUE': [0.01, 0.05]  # Wrong column name
            })
            df.to_csv(input_file, sep='\t', index=False)
            
            with pytest.raises(ValueError):
                apply_fdr_correction(input_file, output_file, p_col='P')

    def test_custom_column_names(self):
        """Test using custom column names."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = os.path.join(tmpdir, 'input.tsv')
            output_file = os.path.join(tmpdir, 'output.tsv')
            
            df = pd.DataFrame({
                'marker': ['rs1', 'rs2'],
                'raw_p': [0.01, 0.05]
            })
            df.to_csv(input_file, sep='\t', index=False)
            
            apply_fdr_correction(
                input_file, 
                output_file, 
                p_col='raw_p', 
                q_col='adjusted_p'
            )
            
            result = pd.read_csv(output_file, sep='\t')
            assert 'adjusted_p' in result.columns
            assert 'raw_p' in result.columns