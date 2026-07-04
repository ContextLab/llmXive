"""
Unit tests for meta_analysis module (T026).

Tests Diebold-Mariano test implementation and Westfall-Young correction.
"""
import pytest
import numpy as np
import pandas as pd
import tempfile
import os
from pathlib import Path
import sys

# Add code root to path for imports
code_root = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_root))

from src.evaluation.meta_analysis import (
    diebold_mariano_test,
    westfall_young_stepdown_maxt,
    run_pairwise_dm_tests,
    meta_analysis
)


class TestDieboldMariano:
    """Tests for the Diebold-Mariano test function."""
    
    def test_identical_forecasts(self):
        """Test that identical forecasts yield p-value ~ 1.0."""
        errors1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        errors2 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        dm_stat, p_value = diebold_mariano_test(errors1, errors2)
        
        assert np.isclose(dm_stat, 0.0, atol=1e-6), "DM stat should be 0 for identical forecasts"
        assert p_value >= 0.9, "P-value should be high for identical forecasts"
    
    def test_different_forecasts(self):
        """Test detection of different forecast accuracy."""
        # One series with consistently smaller errors
        errors1 = np.array([0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2])
        errors2 = np.array([1.0, 2.0, 1.0, 2.0, 1.0, 2.0, 1.0, 2.0, 1.0, 2.0])
        
        dm_stat, p_value = diebold_mariano_test(errors1, errors2)
        
        assert dm_stat != 0.0, "DM stat should be non-zero for different forecasts"
        assert p_value < 0.5, "P-value should be lower for different forecasts"
    
    def test_mismatched_lengths(self):
        """Test that mismatched lengths raise an error."""
        errors1 = np.array([1.0, 2.0, 3.0])
        errors2 = np.array([1.0, 2.0])
        
        with pytest.raises(ValueError, match="equal length"):
            diebold_mariano_test(errors1, errors2)
    
    def test_small_sample_warning(self):
        """Test warning for small sample size."""
        errors1 = np.array([1.0, 2.0, 3.0])
        errors2 = np.array([1.5, 2.5, 3.5])
        
        # Should not raise, but may log a warning
        dm_stat, p_value = diebold_mariano_test(errors1, errors2)
        assert not np.isnan(dm_stat)
        assert not np.isnan(p_value)


class TestWestfallYoung:
    """Tests for Westfall-Young correction."""
    
    def test_single_test(self):
        """Test correction with a single test."""
        p_values = np.array([0.03])
        test_names = ["A vs B"]
        errors_dict = {
            "A": np.array([0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2]),
            "B": np.array([1.0, 2.0, 1.0, 2.0, 1.0, 2.0, 1.0, 2.0, 1.0, 2.0])
        }
        
        adjusted, corrected = westfall_young_stepdown_maxt(
            p_values, test_names, errors_dict, n_permutations=100, random_seed=42
        )
        
        assert len(adjusted) == 1
        assert 0 <= adjusted[0] <= 1
        assert "A vs B" in corrected
    
    def test_multiple_tests(self):
        """Test correction with multiple tests."""
        p_values = np.array([0.01, 0.05, 0.20])
        test_names = ["A vs B", "A vs C", "B vs C"]
        errors_dict = {
            "A": np.array([0.1] * 50),
            "B": np.array([1.0] * 50),
            "C": np.array([0.5] * 50)
        }
        
        adjusted, corrected = westfall_young_stepdown_maxt(
            p_values, test_names, errors_dict, n_permutations=100, random_seed=42
        )
        
        assert len(adjusted) == 3
        assert all(0 <= p <= 1 for p in adjusted)
        assert len(corrected) == 3
    
    def test_adjusted_p_values_larger(self):
        """Test that adjusted p-values are generally larger than raw."""
        p_values = np.array([0.01, 0.02, 0.03])
        test_names = ["A vs B", "A vs C", "B vs C"]
        errors_dict = {
            "A": np.array([0.1] * 100),
            "B": np.array([1.0] * 100),
            "C": np.array([0.5] * 100)
        }
        
        adjusted, _ = westfall_young_stepdown_maxt(
            p_values, test_names, errors_dict, n_permutations=200, random_seed=42
        )
        
        # Westfall-Young is conservative; adjusted should be >= raw in most cases
        # (with permutation noise, this is probabilistic)
        assert np.mean(adjusted >= p_values) >= 0.5, "Adjusted p-values should generally be larger"


class TestRunPairwiseDM:
    """Tests for pairwise DM test execution."""
    
    def test_pairwise_comparisons(self):
        """Test that pairwise comparisons are generated correctly."""
        forecast_data = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=20),
            'method': ['A'] * 10 + ['B'] * 10,
            'forecast_value': [0.5] * 20,
            'actual': [0.55] * 10 + [0.45] * 10
        })
        
        # Restructure for proper testing
        forecast_data = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=10).tolist() * 2,
            'method': ['A'] * 10 + ['B'] * 10,
            'forecast_value': [0.5] * 10 + [0.6] * 10,
            'actual': [0.55] * 10 + [0.45] * 10
        })
        
        actual_outcomes = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=10),
            'actual_vote_share': [0.55] * 10
        })
        
        results_df, errors_dict = run_pairwise_dm_tests(forecast_data, actual_outcomes)
        
        assert 'comparison' in results_df.columns
        assert 'raw_p_value' in results_df.columns
        assert len(results_df) > 0  # At least one comparison
        assert 'A' in errors_dict
        assert 'B' in errors_dict

class TestMetaAnalysisIntegration:
    """Integration tests for the full meta_analysis function."""
    
    def test_full_pipeline(self):
        """Test the complete meta-analysis pipeline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create temporary forecast results
            forecast_path = os.path.join(tmpdir, "forecasts.csv")
            forecast_data = pd.DataFrame({
                'date': pd.date_range('2020-01-01', periods=50).tolist() * 2,
                'method': ['simple_avg'] * 50 + ['weighted_avg'] * 50,
                'forecast_value': [0.5] * 50 + [0.52] * 50,
                'actual': [0.51] * 50 + [0.49] * 50
            })
            forecast_data.to_csv(forecast_path, index=False)
            
            # Create temporary actual outcomes
            outcomes_path = os.path.join(tmpdir, "outcomes.csv")
            outcomes_data = pd.DataFrame({
                'date': pd.date_range('2020-01-01', periods=50),
                'actual_vote_share': [0.51] * 50
            })
            outcomes_data.to_csv(outcomes_path, index=False)
            
            output_path = os.path.join(tmpdir, "meta_results.csv")
            
            # Run meta-analysis with small permutation count for speed
            results = meta_analysis(
                forecast_path,
                outcomes_path,
                output_path,
                n_permutations=50,  # Small for testing
                random_seed=42
            )
            
            assert os.path.exists(output_path)
            assert 'westfall_young_p_value' in results.columns
            assert 'significant_at_0.05' in results.columns
            assert len(results) > 0
            
            # Verify output file content
            saved_results = pd.read_csv(output_path)
            assert len(saved_results) == len(results)
            assert 'westfall_young_p_value' in saved_results.columns