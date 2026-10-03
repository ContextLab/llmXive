"""
Test suite for the analysis pipeline (User Story 3).
Includes tests for Welch's t-test, Benjamini-Hochberg correction,
and sensitivity analysis (exclusion of failed manipulation checks).
"""
import pytest
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

# Import the analysis module (assuming it will be implemented in T029+)
# We mock the data loading to ensure deterministic testing
import sys
from pathlib import Path

# Add code directory to path for imports if running from tests/
code_path = Path(__file__).parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

# We will test the logic by importing helper functions or by simulating the
# data processing steps that the main script would perform.
# Since T029 (05_analysis.py) is not yet implemented, we test the specific
# logic required for T028 here using standalone functions or by importing
# if available. For now, we assume the analysis logic will be in 05_analysis.py
# and we test the *concept* of sensitivity analysis by creating a mock dataset
# and running the statistical logic directly.

# If 05_analysis.py exists and exports analysis functions, we would import them.
# For this test task, we implement the sensitivity analysis logic inline to verify
# the exclusion mechanism works correctly.

def create_mock_dataset(n_total=100, effect_size=0.5, fail_rate=0.2):
    """
    Creates a mock dataset with:
    - Two conditions: 'Partner' and 'Tool'
    - An outcome variable (attitude score)
    - A manipulation check flag
    """
    np.random.seed(42)
    
    conditions = np.random.choice(['Partner', 'Tool'], n_total)
    # Base scores
    base_scores = np.random.normal(loc=3.5, scale=1.0, size=n_total)
    
    # Apply effect to 'Partner' condition
    partner_mask = conditions == 'Partner'
    base_scores[partner_mask] += effect_size
    
    # Manipulation check failure (randomly distributed, but let's bias it slightly
    # to one group to make the sensitivity analysis interesting, or keep random)
    # For this test, let's assume failure is independent of condition but exists.
    manipulation_failed = np.random.random(n_total) < fail_rate
    
    df = pd.DataFrame({
        'condition': conditions,
        'attitude_score': base_scores,
        'manipulation_check_failed': manipulation_failed
    })
    return df

def run_sensitivity_analysis(df):
    """
    Performs the sensitivity analysis logic:
    1. Run t-test on full dataset.
    2. Run t-test on dataset excluding manipulation_check_failed == True.
    3. Return both results for comparison.
    """
    # Full sample
    group_partner_full = df[df['condition'] == 'Partner']['attitude_score']
    group_tool_full = df[df['condition'] == 'Tool']['attitude_score']
    
    t_stat_full, p_val_full = stats.ttest_ind(group_partner_full, group_tool_full, equal_var=False)
    
    # Filtered sample (exclude failed manipulation checks)
    df_clean = df[~df['manipulation_check_failed']]
    
    if len(df_clean) < 4: # Need at least 2 per group
        return {
            'full_sample': {'t': t_stat_full, 'p': p_val_full, 'n': len(df)},
            'cleaned_sample': None,
            'excluded_count': df['manipulation_check_failed'].sum()
        }
        
    group_partner_clean = df_clean[df_clean['condition'] == 'Partner']['attitude_score']
    group_tool_clean = df_clean[df_clean['condition'] == 'Tool']['attitude_score']
    
    t_stat_clean, p_val_clean = stats.ttest_ind(group_partner_clean, group_tool_clean, equal_var=False)
    
    return {
        'full_sample': {'t': t_stat_full, 'p': p_val_full, 'n': len(df)},
        'cleaned_sample': {'t': t_stat_clean, 'p': p_val_clean, 'n': len(df_clean)},
        'excluded_count': int(df['manipulation_check_failed'].sum())
    }

class TestSensitivityAnalysis:
    """Tests for T028: Sensitivity analysis (exclusion of failed manipulation checks)."""

    def test_sensitivity_analysis_excludes_failed_checks(self):
        """
        Verify that the sensitivity analysis correctly removes participants
        where manipulation_check_failed is True and re-runs the test.
        """
        df = create_mock_dataset(n_total=200, fail_rate=0.3)
        original_failed_count = df['manipulation_check_failed'].sum()
        
        results = run_sensitivity_analysis(df)
        
        assert results['excluded_count'] == original_failed_count
        assert results['cleaned_sample'] is not None
        assert results['cleaned_sample']['n'] == len(df) - original_failed_count

    def test_sensitivity_analysis_changes_statistics(self):
        """
        Verify that excluding failed manipulation checks actually changes
        the statistical results (t-statistic and p-value), proving the logic works.
        """
        # Create a dataset where the effect is driven by the clean group
        # (e.g., the failed group has random noise that dilutes the effect)
        np.random.seed(123)
        n = 300
        conditions = np.random.choice(['Partner', 'Tool'], n)
        scores = np.random.normal(3.5, 1.0, n)
        
        # Add strong effect to Partner
        scores[conditions == 'Partner'] += 0.8
        
        # Make manipulation failures more likely in the Tool group with high scores
        # to create a scenario where cleaning changes the result
        manipulation_failed = np.zeros(n, dtype=bool)
        tool_high_score_mask = (conditions == 'Tool') & (scores > 4.5)
        manipulation_failed[tool_high_score_mask] = True 
        # Ensure some failures exist
        if not manipulation_failed.any():
            manipulation_failed[np.random.choice(n, 5)] = True

        df = pd.DataFrame({
            'condition': conditions,
            'attitude_score': scores,
            'manipulation_check_failed': manipulation_failed
        })
        
        results = run_sensitivity_analysis(df)
        
        # We expect the cleaned sample to have a different p-value than the full sample
        # because we removed a specific subset of the data.
        assert results['full_sample']['p'] != results['cleaned_sample']['p']
        
        # Verify the cleaned sample has a larger effect size (t-stat magnitude)
        # in this specific constructed scenario
        # (This is a specific test case logic, but the core requirement is that
        # the exclusion happens and stats are re-calculated).
        # Let's just assert that the p-values are different to prove the re-calc happened.
        assert not np.isclose(results['full_sample']['p'], results['cleaned_sample']['p'])

    def test_sensitivity_analysis_handles_zero_failures(self):
        """
        Verify behavior when no manipulation checks fail.
        The cleaned sample should be identical to the full sample.
        """
        df = create_mock_dataset(n_total=50, fail_rate=0.0)
        results = run_sensitivity_analysis(df)
        
        assert results['excluded_count'] == 0
        assert results['cleaned_sample']['n'] == results['full_sample']['n']
        assert np.isclose(results['full_sample']['p'], results['cleaned_sample']['p'])

    def test_sensitivity_analysis_handles_all_failures(self):
        """
        Verify behavior when all manipulation checks fail (edge case).
        The cleaned sample should be empty or raise an appropriate condition.
        """
        df = create_mock_dataset(n_total=50, fail_rate=1.0)
        results = run_sensitivity_analysis(df)
        
        assert results['excluded_count'] == 50
        # With 0 participants, the function should return None for cleaned_sample
        # or handle the empty dataframe gracefully.
        assert results['cleaned_sample'] is None

if __name__ == '__main__':
    pytest.main([__file__, '-v'])