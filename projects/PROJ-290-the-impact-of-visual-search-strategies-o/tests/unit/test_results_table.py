"""
Unit tests for the statistical results table generation (T034).

Tests verify:
- Coefficient extraction from model results
- Adjusted p-value computation
- Combined table generation
- File output correctness
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.results_table import (
    extract_coefficients_table,
    compute_adjusted_pvalues,
    generate_combined_results_table,
    generate_results_summary
)

@pytest.fixture
def mock_primary_results():
    """Mock primary LMM results dictionary."""
    return {
        'fixed_effects': [
            {
                'term': 'intercept',
                'estimate': 2.5,
                'std_error': 0.15,
                't_value': 16.67,
                'p_value': 0.0001
            },
            {
                'term': 'continuous_ratio',
                'estimate': -0.45,
                'std_error': 0.12,
                't_value': -3.75,
                'p_value': 0.002
            }
        ],
        'model_info': {
            'converged': True,
            'n_iterations': 50
        }
    }

@pytest.fixture
def mock_exploratory_results():
    """Mock exploratory LMM results dictionary."""
    return {
        'fixed_effects': [
            {
                'term': 'intercept',
                'estimate': 2.6,
                'std_error': 0.18,
                't_value': 14.44,
                'p_value': 0.0001
            },
            {
                'term': 'cluster_strategy_A',
                'estimate': -0.30,
                'std_error': 0.14,
                't_value': -2.14,
                'p_value': 0.035
            },
            {
                'term': 'cluster_strategy_B',
                'estimate': 0.15,
                'std_error': 0.16,
                't_value': 0.94,
                'p_value': 0.350
            }
        ],
        'model_info': {
            'converged': True,
            'n_iterations': 45
        }
    }

@pytest.fixture
def mock_permutation_results():
    """Mock permutation test results."""
    return {
        'observed_t': -3.75,
        'null_mean': 0.02,
        'p_value': 0.004,
        'n_iterations': 1000
    }

class TestExtractCoefficientsTable:
    """Tests for coefficient extraction."""

    def test_extract_primary_coefficients(self, mock_primary_results):
        """Test extraction of primary model coefficients."""
        df = extract_coefficients_table(mock_primary_results, model_type='primary')
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert 'term' in df.columns
        assert 'estimate' in df.columns
        assert 'model_type' in df.columns
        assert df['model_type'].iloc[0] == 'primary'
        
        # Check specific values
        ratio_row = df[df['term'] == 'continuous_ratio']
        assert len(ratio_row) == 1
        assert abs(ratio_row['estimate'].iloc[0] - (-0.45)) < 0.001

    def test_extract_empty_results(self):
        """Test extraction from empty results."""
        df = extract_coefficients_table({'fixed_effects': []}, model_type='primary')
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_extract_missing_fixed_effects(self):
        """Test extraction when fixed_effects key is missing."""
        df = extract_coefficients_table({}, model_type='primary')
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

class TestComputeAdjustedPvalues:
    """Tests for adjusted p-value computation."""

    def test_adjusted_pvalues_computation(self):
        """Test that adjusted p-values are computed correctly."""
        df = pd.DataFrame({
            'term': ['intercept', 'predictor1', 'predictor2'],
            'p_value': [0.001, 0.025, 0.150]
        })
        
        df_adjusted = compute_adjusted_pvalues(df, method='fdr_bh')
        
        assert 'p_adjusted' in df_adjusted.columns
        assert len(df_adjusted) == 3
        assert not df_adjusted['p_adjusted'].isna().all()
        
        # Check that adjusted p-values are >= original p-values
        assert all(df_adjusted['p_adjusted'] >= df_adjusted['p_value'])

    def test_adjusted_pvalues_empty_dataframe(self):
        """Test adjustment on empty DataFrame."""
        df = pd.DataFrame(columns=['term', 'p_value'])
        df_adjusted = compute_adjusted_pvalues(df)
        assert 'p_adjusted' in df_adjusted.columns

    def test_adjusted_pvalues_no_pvalues(self):
        """Test adjustment when no p-values exist."""
        df = pd.DataFrame({'term': ['a', 'b']})
        df_adjusted = compute_adjusted_pvalues(df)
        assert 'p_adjusted' in df_adjusted.columns
        assert df_adjusted['p_adjusted'].isna().all()

class TestGenerateCombinedResultsTable:
    """Tests for combined table generation."""

    def test_combined_table_creation(self, mock_primary_results, mock_exploratory_results):
        """Test creation of combined table from both models."""
        combined = generate_combined_results_table(mock_primary_results, mock_exploratory_results)
        
        assert isinstance(combined, pd.DataFrame)
        assert len(combined) == 5  # 2 from primary + 3 from exploratory
        assert 'model_type' in combined.columns
        assert 'p_adjusted' in combined.columns
        
        # Check model type distribution
        assert combined[combined['model_type'] == 'primary'].shape[0] == 2
        assert combined[combined['model_type'] == 'exploratory'].shape[0] == 3

    def test_combined_table_primary_only(self, mock_primary_results):
        """Test combined table with only primary results."""
        combined = generate_combined_results_table(mock_primary_results, None)
        
        assert isinstance(combined, pd.DataFrame)
        assert len(combined) == 2
        assert all(combined['model_type'] == 'primary')

    def test_combined_table_empty(self):
        """Test combined table with no results."""
        combined = generate_combined_results_table({}, None)
        assert isinstance(combined, pd.DataFrame)
        assert len(combined) == 0

class TestGenerateResultsSummary:
    """Tests for results summary generation."""

    def test_summary_generation(self, mock_primary_results, mock_permutation_results):
        """Test summary generation with primary and permutation results."""
        combined = generate_combined_results_table(mock_primary_results, None)
        summary = generate_results_summary(combined, mock_permutation_results)
        
        assert isinstance(summary, dict)
        assert 'primary_analysis' in summary
        assert 'permutation_test' in summary
        assert 'total_tests' in summary
        assert summary['total_tests'] == 2
        
        # Check primary analysis details
        assert 'coefficient' in summary['primary_analysis']
        assert 'p_value' in summary['primary_analysis']
        assert 'significant' in summary['primary_analysis']

    def test_summary_without_permutation(self, mock_primary_results):
        """Test summary generation without permutation results."""
        combined = generate_combined_results_table(mock_primary_results, None)
        summary = generate_results_summary(combined, None)
        
        assert summary['permutation_test'] is None
        assert 'primary_analysis' in summary

    def test_summary_empty_table(self):
        """Test summary from empty table."""
        combined = pd.DataFrame()
        summary = generate_results_summary(combined)
        
        assert summary['total_tests'] == 0
        assert summary['significant_tests'] == 0

class TestIntegration:
    """Integration tests for the results table pipeline."""

    def test_full_pipeline_with_temp_files(self, mock_primary_results, mock_exploratory_results):
        """Test the full pipeline including file operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Save mock results
            primary_path = tmpdir / 'lmm_continuous.json'
            exploratory_path = tmpdir / 'lmm_cluster.json'
            
            with open(primary_path, 'w') as f:
                json.dump(mock_primary_results, f)
            
            with open(exploratory_path, 'w') as f:
                json.dump(mock_exploratory_results, f)
            
            # Load and process
            from analysis.results_table import load_lmm_results, generate_combined_results_table, compute_adjusted_pvalues
            
            primary, exploratory = load_lmm_results(primary_path, exploratory_path)
            combined = generate_combined_results_table(primary, exploratory)
            combined = compute_adjusted_pvalues(combined)
            
            assert len(combined) == 5
            assert 'p_adjusted' in combined.columns
            assert not combined['p_adjusted'].isna().all()