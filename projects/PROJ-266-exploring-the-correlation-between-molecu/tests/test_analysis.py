import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from scipy import stats

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.data.analysis import (
    calculate_correlations,
    apply_benjamini_hochberg,
    write_correlation_results,
    write_fdr_results,
    load_analysis_data
)
from code.utils.config import get_project_root


class TestCorrelationLogic:
    """Unit tests for correlation calculation logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_data = pd.DataFrame({
            'smiles': ['CCO', 'CC(=O)O', 'c1ccccc1', 'CC(C)C', 'CCCC'],
            'logPapp': [-4.5, -5.2, -3.8, -4.9, -4.1],
            'dihedral_variance': [1.2, 0.8, 2.1, 0.9, 1.5],
            'logP': [-0.3, -0.3, 2.1, 2.0, 2.0],
            'mw': [46.0, 60.0, 78.0, 58.0, 58.0],
            'psa': [20.2, 37.3, 0.0, 0.0, 0.0]
        })
        self.expected_columns = ['metric', 'correlation', 'p_value', 'significant']

    def test_correlation_calculation_returns_correct_structure(self):
        """Test that calculate_correlations returns expected DataFrame structure."""
        results = calculate_correlations(self.test_data, 'dihedral_variance', 'logPapp')
        
        assert isinstance(results, pd.DataFrame)
        assert 'metric' in results.columns
        assert 'correlation' in results.columns
        assert 'p_value' in results.columns
        assert 'significant' in results.columns
        assert len(results) > 0

    def test_correlation_values_are_valid(self):
        """Test that correlation coefficients are within [-1, 1]."""
        results = calculate_correlations(self.test_data, 'dihedral_variance', 'logPapp')
        
        for _, row in results.iterrows():
            assert -1.0 <= row['correlation'] <= 1.0, f"Correlation {row['correlation']} out of bounds"
            assert 0.0 <= row['p_value'] <= 1.0, f"P-value {row['p_value']} out of bounds"

    def test_pearson_correlation_sign(self):
        """Test that Pearson correlation sign matches manual calculation."""
        results = calculate_correlations(self.test_data, 'dihedral_variance', 'logPapp')
        
        # Find Pearson result
        pearson_row = results[results['metric'] == 'pearson'].iloc[0]
        
        # Manual calculation
        x = self.test_data['dihedral_variance']
        y = self.test_data['logPapp']
        manual_corr, manual_p = stats.pearsonr(x, y)
        
        assert np.isclose(pearson_row['correlation'], manual_corr, rtol=1e-5)
        assert np.isclose(pearson_row['p_value'], manual_p, rtol=1e-5)

    def test_spearman_correlation_sign(self):
        """Test that Spearman correlation sign matches manual calculation."""
        results = calculate_correlations(self.test_data, 'dihedral_variance', 'logPapp')
        
        # Find Spearman result
        spearman_row = results[results['metric'] == 'spearman'].iloc[0]
        
        # Manual calculation
        x = self.test_data['dihedral_variance']
        y = self.test_data['logPapp']
        manual_corr, manual_p = stats.spearmanr(x, y)
        
        assert np.isclose(spearman_row['correlation'], manual_corr, rtol=1e-5)
        assert np.isclose(spearman_row['p_value'], manual_p, rtol=1e-5)

    def test_significance_flagging(self):
        """Test that significance flag is correctly set based on p-value threshold."""
        results = calculate_correlations(self.test_data, 'dihedral_variance', 'logPapp')
        
        for _, row in results.iterrows():
            expected_sig = row['p_value'] < 0.05
            assert row['significant'] == expected_sig, \
                f"Significance flag mismatch for {row['metric']}: expected {expected_sig}, got {row['significant']}"


class TestFDRLogic:
    """Unit tests for Benjamini-Hochberg FDR correction logic."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create test data with known p-values
        self.test_results = pd.DataFrame({
            'metric': ['pearson', 'spearman', 'partial_pearson', 'partial_spearman'],
            'correlation': [0.8, 0.75, 0.6, 0.55],
            'p_value': [0.01, 0.03, 0.04, 0.08]
        })

    def test_bh_correction_returns_q_values(self):
        """Test that apply_benjamini_hochberg returns q-values."""
        q_values = apply_benjamini_hochberg(self.test_results['p_value'].values)
        
        assert len(q_values) == len(self.test_results)
        assert all(q >= 0 for q in q_values)
        assert all(q <= 1 for q in q_values)

    def test_bh_correction_monotonicity(self):
        """Test that q-values are monotonically non-decreasing with rank."""
        p_values = np.array([0.01, 0.03, 0.04, 0.08])
        q_values = apply_benjamini_hochberg(p_values)
        
        # After BH correction, q-values should be monotonically increasing
        # (or at least non-decreasing) when sorted by original p-value order
        for i in range(len(q_values) - 1):
            assert q_values[i] <= q_values[i + 1] or np.isclose(q_values[i], q_values[i + 1]), \
                f"Q-values not monotonic: {q_values}"

    def test_bh_correction_with_known_values(self):
        """Test BH correction against manual calculation for known input."""
        # Manual BH calculation for p = [0.01, 0.03, 0.04, 0.08] with n=4:
        # Sorted p: [0.01, 0.03, 0.04, 0.08]
        # Rank: [1, 2, 3, 4]
        # BH threshold: [0.01*4/1=0.04, 0.03*4/2=0.06, 0.04*4/3=0.053, 0.08*4/4=0.08]
        # q-values (cumulative min from end): [0.04, 0.053, 0.053, 0.08]
        
        p_values = np.array([0.01, 0.03, 0.04, 0.08])
        q_values = apply_benjamini_hochberg(p_values)
        
        expected_q = [0.04, 0.05333333333333333, 0.05333333333333333, 0.08]
        
        for i, (q, exp) in enumerate(zip(q_values, expected_q)):
            assert np.isclose(q, exp, rtol=1e-5), \
                f"Q-value mismatch at index {i}: expected {exp}, got {q}"

    def test_bh_correction_preserves_order(self):
        """Test that BH correction preserves the order of p-values."""
        p_values = np.array([0.01, 0.03, 0.04, 0.08])
        q_values = apply_benjamini_hochberg(p_values)
        
        # The rank order should be preserved
        p_ranks = np.argsort(p_values)
        q_ranks = np.argsort(q_values)
        
        assert np.array_equal(p_ranks, q_ranks), \
            "BH correction should preserve the rank order of p-values"


class TestWriteResults:
    """Unit tests for writing correlation and FDR results to files."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir)
        
        # Create mock data
        self.correlation_results = pd.DataFrame({
            'metric': ['pearson', 'spearman'],
            'correlation': [0.8, 0.75],
            'p_value': [0.01, 0.03],
            'significant': [True, True]
        })
        
        self.fdr_results = pd.DataFrame({
            'metric': ['pearson', 'spearman'],
            'correlation': [0.8, 0.75],
            'p_value': [0.01, 0.03],
            'q_value': [0.04, 0.053],
            'significant': [True, True],
            'fdr_significant': [True, True]
        })

    def teardown_method(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_write_correlation_results_creates_file(self):
        """Test that write_correlation_results creates the output file."""
        output_path = Path(self.test_dir) / 'correlation_results.csv'
        write_correlation_results(self.correlation_results, str(output_path))
        
        assert output_path.exists(), "Correlation results file was not created"
        
        # Verify file content
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == len(self.correlation_results)
        assert list(loaded_df.columns) == list(self.correlation_results.columns)

    def test_write_fdr_results_creates_file(self):
        """Test that write_fdr_results creates the output file."""
        output_path = Path(self.test_dir) / 'fdr_corrected_results.csv'
        write_fdr_results(self.fdr_results, str(output_path))
        
        assert output_path.exists(), "FDR results file was not created"
        
        # Verify file content
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == len(self.fdr_results)
        assert 'q_value' in loaded_df.columns
        assert 'fdr_significant' in loaded_df.columns

    def test_write_results_with_empty_dataframe(self):
        """Test that writing empty DataFrames doesn't crash."""
        empty_correlation = pd.DataFrame(columns=['metric', 'correlation', 'p_value', 'significant'])
        empty_fdr = pd.DataFrame(columns=['metric', 'correlation', 'p_value', 'q_value', 'significant', 'fdr_significant'])
        
        output_path_correlation = Path(self.test_dir) / 'empty_correlation.csv'
        output_path_fdr = Path(self.test_dir) / 'empty_fdr.csv'
        
        write_correlation_results(empty_correlation, str(output_path_correlation))
        write_fdr_results(empty_fdr, str(output_path_fdr))
        
        assert output_path_correlation.exists()
        assert output_path_fdr.exists()


class TestEndToEnd:
    """Integration tests for the full correlation and FDR pipeline."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir)
        
        # Create realistic test data
        np.random.seed(42)
        n_samples = 100
        self.test_data = pd.DataFrame({
            'smiles': [f'CCO_{i}' for i in range(n_samples)],
            'logPapp': np.random.normal(-4.5, 0.8, n_samples),
            'dihedral_variance': np.random.normal(1.5, 0.5, n_samples),
            'logP': np.random.normal(1.0, 0.5, n_samples),
            'mw': np.random.normal(300, 50, n_samples),
            'psa': np.random.normal(50, 20, n_samples)
        })

    def teardown_method(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_full_correlation_and_fdr_pipeline(self):
        """Test the complete pipeline from correlation calculation to FDR correction."""
        # Step 1: Calculate correlations
        correlation_results = calculate_correlations(
            self.test_data, 
            'dihedral_variance', 
            'logPapp'
        )
        
        assert len(correlation_results) > 0
        assert 'p_value' in correlation_results.columns
        
        # Step 2: Apply FDR correction
        q_values = apply_benjamini_hochberg(correlation_results['p_value'].values)
        correlation_results['q_value'] = q_values
        correlation_results['fdr_significant'] = q_values < 0.05
        
        # Step 3: Write results
        output_path = Path(self.test_dir) / 'test_results.csv'
        write_fdr_results(correlation_results, str(output_path))
        
        # Step 4: Verify output
        assert output_path.exists()
        loaded_results = pd.read_csv(output_path)
        
        assert 'q_value' in loaded_results.columns
        assert 'fdr_significant' in loaded_results.columns
        assert len(loaded_results) == len(correlation_results)

    def test_pipeline_with_no_significant_results(self):
        """Test pipeline when no correlations are significant after FDR."""
        # Create data with no correlation
        self.test_data['logPapp'] = np.random.normal(-4.5, 0.8, len(self.test_data))
        self.test_data['dihedral_variance'] = np.random.normal(1.5, 0.5, len(self.test_data))
        
        correlation_results = calculate_correlations(
            self.test_data, 
            'dihedral_variance', 
            'logPapp'
        )
        
        q_values = apply_benjamini_hochberg(correlation_results['p_value'].values)
        correlation_results['q_value'] = q_values
        correlation_results['fdr_significant'] = q_values < 0.05
        
        # At least some should be non-significant
        assert any(~correlation_results['fdr_significant']), \
            "Expected some non-significant results in random data"

    def test_pipeline_handles_multiple_metrics(self):
        """Test pipeline with multiple correlation metrics."""
        correlation_results = calculate_correlations(
            self.test_data, 
            'dihedral_variance', 
            'logPapp'
        )
        
        # Should have multiple metrics (pearson, spearman, etc.)
        assert len(correlation_results['metric'].unique()) > 1, \
            f"Expected multiple metrics, got {correlation_results['metric'].unique()}"
        
        # Apply FDR correction
        q_values = apply_benjamini_hochberg(correlation_results['p_value'].values)
        correlation_results['q_value'] = q_values
        correlation_results['fdr_significant'] = q_values < 0.05
        
        # Verify all metrics have q-values
        assert len(correlation_results['q_value']) == len(correlation_results)
        assert all(0 <= q <= 1 for q in correlation_results['q_value'])