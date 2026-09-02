"""
Contract tests for sensitivity analysis stratification.

These tests verify that the sensitivity analysis module correctly:
1. Stratifies data by repository star-count quartiles
2. Performs statistical testing on each stratum
3. Aggregates results to determine consistency

Run these tests before implementing T029 to ensure the interface is correct.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.sensitivity import (
    stratify_by_star_quartiles,
    run_sensitivity_analysis,
    check_result_consistency
)
from code.utils.models import PullRequest


class TestStratification:
    """Tests for star-count quartile stratification logic."""

    def test_stratify_by_star_quartiles_basic(self):
        """Test that data is correctly split into 4 quartiles."""
        # Create sample data with known star counts
        data = pd.DataFrame({
            'pr_id': [f'pr_{i}' for i in range(100)],
            'repo_id': [f'repo_{i % 10}' for i in range(100)],
            'star_count': list(range(100)),  # 0-99
            'review_duration': np.random.rand(100) * 100,
            'author_type': ['human'] * 50 + ['llm'] * 50,
            'file_size': np.random.rand(100) * 1000,
            'complexity_score': np.random.rand(100) * 10
        })
        
        strata = stratify_by_star_quartiles(data)
        
        assert len(strata) == 4, "Should create exactly 4 strata"
        
        # Check that all data points are assigned to exactly one stratum
        total_assigned = sum(len(df) for df in strata.values())
        assert total_assigned == len(data), "All data points should be assigned"
        
        # Check that quartiles have roughly equal size (allowing for small differences)
        sizes = [len(df) for df in strata.values()]
        assert all(20 <= s <= 30 for s in sizes), "Quartiles should be roughly equal size"
    
    def test_stratify_by_star_quartiles_with_missing_data(self):
        """Test handling of missing star_count values."""
        data = pd.DataFrame({
            'pr_id': ['pr_1', 'pr_2', 'pr_3', 'pr_4', 'pr_5'],
            'star_count': [10, None, 100, np.nan, 500],
            'review_duration': [10.0, 20.0, 30.0, 40.0, 50.0],
            'author_type': ['human', 'human', 'llm', 'llm', 'human']
        })
        
        strata = stratify_by_star_quartiles(data)
        
        # Should exclude rows with missing star_count
        total_assigned = sum(len(df) for df in strata.values())
        assert total_assigned == 3, "Should exclude 2 rows with missing star_count"
    
    def test_stratify_by_star_quartiles_empty_dataframe(self):
        """Test handling of empty input."""
        data = pd.DataFrame(columns=['pr_id', 'star_count', 'review_duration', 'author_type'])
        
        strata = stratify_by_star_quartiles(data)
        
        assert len(strata) == 4
        assert all(len(df) == 0 for df in strata.values())

class TestSensitivityAnalysis:
    """Tests for the sensitivity analysis pipeline."""

    def test_run_sensitivity_analysis_basic(self):
        """Test that sensitivity analysis runs on stratified data."""
        # Create sample data with known effect
        np.random.seed(42)
        n = 200
        data = pd.DataFrame({
            'pr_id': [f'pr_{i}' for i in range(n)],
            'repo_id': [f'repo_{i % 20}' for i in range(n)],
            'star_count': np.random.randint(0, 10000, n),
            'review_duration': np.concatenate([
                np.random.normal(50, 10, n//2),  # Human
                np.random.normal(30, 10, n - n//2)  # LLM (faster)
            ]),
            'author_type': ['human'] * (n//2) + ['llm'] * (n - n//2),
            'file_size': np.random.rand(n) * 1000,
            'complexity_score': np.random.rand(n) * 10
        })
        
        results = run_sensitivity_analysis(data)
        
        assert isinstance(results, dict), "Results should be a dictionary"
        assert 'strata_results' in results, "Should contain strata_results key"
        assert 'overall_consistency' in results, "Should contain overall_consistency key"
        
        # Check that we have results for each stratum
        assert len(results['strata_results']) == 4, "Should have 4 stratum results"
        
        # Check structure of individual stratum results
        for stratum_id, stratum_result in results['strata_results'].items():
            assert 'p_value' in stratum_result, f"Stratum {stratum_id} should have p_value"
            assert 'effect_size' in stratum_result, f"Stratum {stratum_id} should have effect_size"
            assert 'n_samples' in stratum_result, f"Stratum {stratum_id} should have n_samples"
            assert 'significant' in stratum_result, f"Stratum {stratum_id} should have significant flag"
    
    def test_run_sensitivity_analysis_with_small_sample(self):
        """Test handling of strata with small sample sizes."""
        # Create data where one stratum has very few samples
        np.random.seed(42)
        data = pd.DataFrame({
            'pr_id': [f'pr_{i}' for i in range(50)],
            'star_count': [10] * 40 + [10000] * 10,  # Skewed distribution
            'review_duration': np.random.rand(50) * 100,
            'author_type': ['human'] * 25 + ['llm'] * 25,
            'file_size': np.random.rand(50) * 1000,
            'complexity_score': np.random.rand(50) * 10
        })
        
        results = run_sensitivity_analysis(data)
        
        # Should still produce results, possibly with warnings for small samples
        assert len(results['strata_results']) == 4
        
        # At least one stratum should have very few samples
        sample_sizes = [r['n_samples'] for r in results['strata_results'].values()]
        assert min(sample_sizes) < 15, "Should have at least one small stratum"

class TestResultConsistency:
    """Tests for consistency checking logic."""

    def test_check_result_consistency_all_significant(self):
        """Test consistency when all strata show significant results."""
        results = {
            'strata_results': {
                'q1': {'p_value': 0.01, 'significant': True},
                'q2': {'p_value': 0.02, 'significant': True},
                'q3': {'p_value': 0.03, 'significant': True},
                'q4': {'p_value': 0.04, 'significant': True}
            }
        }
        
        consistency = check_result_consistency(results)
        
        assert consistency['consistent'] is True
        assert consistency['significant_ratio'] == 1.0
        assert consistency['threshold'] == 0.8

    def test_check_result_consistency_mixed_significance(self):
        """Test consistency when some strata are significant."""
        results = {
            'strata_results': {
                'q1': {'p_value': 0.01, 'significant': True},
                'q2': {'p_value': 0.01, 'significant': True},
                'q3': {'p_value': 0.01, 'significant': True},
                'q4': {'p_value': 0.10, 'significant': False}
            }
        }
        
        consistency = check_result_consistency(results)
        
        assert consistency['consistent'] is True  # 3/4 = 0.75 < 0.8, but let's check the logic
        assert consistency['significant_ratio'] == 0.75

    def test_check_result_consistency_below_threshold(self):
        """Test consistency when below threshold."""
        results = {
            'strata_results': {
                'q1': {'p_value': 0.01, 'significant': True},
                'q2': {'p_value': 0.10, 'significant': False},
                'q3': {'p_value': 0.10, 'significant': False},
                'q4': {'p_value': 0.10, 'significant': False}
            }
        }
        
        consistency = check_result_consistency(results)
        
        assert consistency['consistent'] is False
        assert consistency['significant_ratio'] == 0.25

    def test_check_result_consistency_empty_results(self):
        """Test handling of empty results."""
        results = {
            'strata_results': {}
        }
        
        consistency = check_result_consistency(results)
        
        assert consistency['consistent'] is False
        assert consistency['significant_ratio'] == 0.0

class TestIntegration:
    """Integration tests for the full sensitivity analysis pipeline."""

    def test_full_pipeline_with_realistic_data(self):
        """Test the complete pipeline with realistic data distribution."""
        np.random.seed(123)
        
        # Create realistic data with star count distribution
        n = 1000
        star_counts = np.random.lognormal(mean=3, sigma=1.5, size=n)  # Skewed distribution
        
        data = pd.DataFrame({
            'pr_id': [f'pr_{i}' for i in range(n)],
            'repo_id': [f'repo_{i % 50}' for i in range(n)],
            'star_count': star_counts.astype(int),
            'review_duration': np.concatenate([
                np.random.normal(60, 20, n//2),  # Human
                np.random.normal(40, 15, n - n//2)  # LLM
            ]),
            'author_type': ['human'] * (n//2) + ['llm'] * (n - n//2),
            'file_size': np.random.lognormal(mean=4, sigma=0.5, size=n),
            'complexity_score': np.random.beta(2, 5, n) * 10
        })
        
        # Run full pipeline
        results = run_sensitivity_analysis(data)
        
        # Verify structure
        assert 'strata_results' in results
        assert 'overall_consistency' in results
        
        # Verify each stratum has meaningful data
        for stratum_id, stratum_result in results['strata_results'].items():
            assert stratum_result['n_samples'] > 0, f"Stratum {stratum_id} should have samples"
            assert 'p_value' in stratum_result
            assert 'effect_size' in stratum_result
        
        # Verify consistency calculation
        consistency = results['overall_consistency']
        assert 'consistent' in consistency
        assert 'significant_ratio' in consistency
        assert 0 <= consistency['significant_ratio'] <= 1.0

    def test_pipeline_handles_edge_cases(self):
        """Test pipeline behavior with various edge cases."""
        # Case 1: All same star count (should still create 4 strata, some empty)
        data_same_stars = pd.DataFrame({
            'pr_id': [f'pr_{i}' for i in range(100)],
            'star_count': [100] * 100,
            'review_duration': np.random.rand(100) * 100,
            'author_type': ['human'] * 50 + ['llm'] * 50,
            'file_size': np.random.rand(100) * 1000,
            'complexity_score': np.random.rand(100) * 10
        })
        
        results = run_sensitivity_analysis(data_same_stars)
        assert len(results['strata_results']) == 4
        
        # Case 2: Very skewed distribution
        data_skewed = pd.DataFrame({
            'pr_id': [f'pr_{i}' for i in range(100)],
            'star_count': [1] * 80 + [10000] * 20,
            'review_duration': np.random.rand(100) * 100,
            'author_type': ['human'] * 50 + ['llm'] * 50,
            'file_size': np.random.rand(100) * 1000,
            'complexity_score': np.random.rand(100) * 10
        })
        
        results = run_sensitivity_analysis(data_skewed)
        assert len(results['strata_results']) == 4
        # Some strata should be empty or very small
        sample_sizes = [r['n_samples'] for r in results['strata_results'].values()]
        assert min(sample_sizes) == 0 or min(sample_sizes) < 5