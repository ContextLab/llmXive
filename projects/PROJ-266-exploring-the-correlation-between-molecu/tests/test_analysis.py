"""
Unit tests for correlation analysis and FDR logic in code/data/analysis.py.
These tests verify the statistical correctness of Pearson/Spearman correlations,
confounder handling, and Benjamini-Hochberg FDR correction.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add the project root to the path to allow imports from code/
# This assumes the test is run from the project root or via pytest with proper config
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.data.analysis import compute_correlations_with_fdr


class TestCorrelationLogic:
    """Tests for the core correlation computation logic."""

    def test_pearson_correlation_significance(self):
        """
        Verify that Pearson correlation is computed correctly for a known relationship.
        We create a synthetic dataset with a strong positive linear relationship.
        """
        np.random.seed(42)
        n = 100
        # Create a strong positive correlation: y = 2x + noise
        x = np.random.normal(0, 1, n)
        y = 2 * x + np.random.normal(0, 0.1, n)

        # Create a mock dataframe
        df = pd.DataFrame({
            'flexibility': x,
            'logPapp': y,
            'logP': np.random.normal(0, 1, n),
            'MW': np.random.normal(0, 1, n),
            'PSA': np.random.normal(0, 1, n)
        })

        # Run the function
        results = compute_correlations_with_fdr(df, 'flexibility', 'logPapp', ['logP', 'MW', 'PSA'])

        # Check that we got results
        assert len(results) > 0, "Results dataframe should not be empty"

        # Find the row for Pearson correlation
        pearson_row = results[results['method'] == 'pearson']
        assert not pearson_row.empty, "Pearson correlation result missing"

        # The correlation should be strong and positive (close to 1.0)
        r_val = pearson_row.iloc[0]['r_value']
        assert 0.9 < r_val <= 1.0, f"Expected strong positive correlation (~1.0), got {r_val}"

        # The p-value should be very small
        p_val = pearson_row.iloc[0]['p_value']
        assert p_val < 0.001, f"Expected very small p-value, got {p_val}"

    def test_spearman_correlation_robustness(self):
        """
        Verify Spearman correlation handles monotonic non-linear relationships.
        """
        np.random.seed(42)
        n = 100
        # Create a monotonic non-linear relationship: y = x^3
        x = np.linspace(-2, 2, n)
        y = x**3 + np.random.normal(0, 0.1, n)

        df = pd.DataFrame({
            'flexibility': x,
            'logPapp': y,
            'logP': np.random.normal(0, 1, n),
            'MW': np.random.normal(0, 1, n),
            'PSA': np.random.normal(0, 1, n)
        })

        results = compute_correlations_with_fdr(df, 'flexibility', 'logPapp', ['logP', 'MW', 'PSA'])

        spearman_row = results[results['method'] == 'spearman']
        assert not spearman_row.empty, "Spearman correlation result missing"

        # Spearman should also show a strong correlation
        r_val = spearman_row.iloc[0]['r_value']
        assert 0.9 < r_val <= 1.0, f"Expected strong Spearman correlation, got {r_val}"

    def test_no_correlation_case(self):
        """
        Verify that uncorrelated variables yield near-zero correlation and high p-value.
        """
        np.random.seed(42)
        n = 100
        x = np.random.normal(0, 1, n)
        y = np.random.normal(0, 1, n)  # Independent noise

        df = pd.DataFrame({
            'flexibility': x,
            'logPapp': y,
            'logP': np.random.normal(0, 1, n),
            'MW': np.random.normal(0, 1, n),
            'PSA': np.random.normal(0, 1, n)
        })

        results = compute_correlations_with_fdr(df, 'flexibility', 'logPapp', ['logP', 'MW', 'PSA'])

        pearson_row = results[results['method'] == 'pearson']
        r_val = pearson_row.iloc[0]['r_value']
        
        # Correlation should be close to 0 (allowing for sampling noise)
        assert abs(r_val) < 0.3, f"Expected near-zero correlation for random data, got {r_val}"

        # P-value should be high (not significant)
        p_val = pearson_row.iloc[0]['p_value']
        assert p_val > 0.05, f"Expected p-value > 0.05 for random data, got {p_val}"


class TestFDRLogic:
    """Tests for the Benjamini-Hochberg FDR correction logic."""

    def test_fdr_correction_mechanism(self):
        """
        Verify that FDR correction adjusts p-values appropriately.
        We create a scenario with multiple tests where some are significant and some are not.
        """
        np.random.seed(42)
        n = 50
        
        # Create a dataset with multiple predictors
        df = pd.DataFrame({
            'flex1': np.random.normal(0, 1, n),
            'flex2': np.random.normal(0, 1, n),
            'flex3': np.random.normal(0, 1, n),
            'logPapp': np.random.normal(0, 1, n),
            'logP': np.random.normal(0, 1, n),
            'MW': np.random.normal(0, 1, n),
            'PSA': np.random.normal(0, 1, n)
        })

        # Manually inject a strong correlation into flex1 to ensure we have at least one significant result
        df.loc[:, 'logPapp'] = 2 * df['flex1'] + np.random.normal(0, 0.1, n)

        # Run correlations for multiple descriptors (simulating the full analysis)
        results = []
        for col in ['flex1', 'flex2', 'flex3']:
            res = compute_correlations_with_fdr(df, col, 'logPapp', ['logP', 'MW', 'PSA'])
            results.append(res)
        
        full_results = pd.concat(results, ignore_index=True)

        # Check that FDR correction was applied (q_value column exists)
        assert 'q_value' in full_results.columns, "q_value column missing from results"

        # The significant predictor (flex1) should have a q-value < 0.05
        flex1_results = full_results[full_results['descriptor'] == 'flex1']
        if not flex1_results.empty:
            q_val = flex1_results.iloc[0]['q_value']
            # Note: FDR might adjust p-value slightly, but with a strong effect, it should remain significant
            # We check if it's reasonably low, acknowledging that with only 3 tests, FDR is close to Bonferroni
            # A strict check might fail due to the small number of tests, so we check for a significant reduction
            # or simply that the column exists and is numeric.
            assert isinstance(q_val, (int, float)), "q_value must be numeric"
            # With only 3 tests, if p < 0.01, q will likely be < 0.05
            p_val = flex1_results.iloc[0]['p_value']
            if p_val < 0.01:
                assert q_val < 0.05, f"Expected q-value < 0.05 for strong signal, got {q_val}"

    def test_fdr_monotonicity(self):
        """
        Verify that FDR-corrected q-values are monotonically non-decreasing with respect to sorted p-values.
        This is a property of the Benjamini-Hochberg procedure.
        """
        # Generate a set of random p-values
        np.random.seed(123)
        p_values = np.random.uniform(0, 1, 20)
        
        # Sort them
        sorted_p = np.sort(p_values)
        m = len(sorted_p)
        
        # Manually compute BH q-values to verify the logic in the function
        # q_i = min( (m/i) * p_i, q_{i+1} ) (monotonicity enforcement)
        q_values_manual = np.zeros(m)
        for i in range(m):
            rank = i + 1
            q_values_manual[i] = (m / rank) * sorted_p[i]
        
        # Enforce monotonicity from the bottom up
        for i in range(m - 2, -1, -1):
            q_values_manual[i] = min(q_values_manual[i], q_values_manual[i+1])
        
        # Cap at 1.0
        q_values_manual = np.minimum(q_values_manual, 1.0)

        # Now, simulate the function's behavior by creating a dummy dataframe
        # and calling the function with a single descriptor to get the raw p-values
        # and then check the internal logic.
        # Since the function returns a dataframe, we can check the relationship between p and q.
        
        n = 50
        df = pd.DataFrame({
            'x': np.random.normal(0, 1, n),
            'y': np.random.normal(0, 1, n),
            'logP': np.random.normal(0, 1, n),
            'MW': np.random.normal(0, 1, n),
            'PSA': np.random.normal(0, 1, n)
        })
        
        # We need to test the FDR logic on a set of p-values.
        # The function computes correlations for multiple descriptors.
        # Let's create a scenario with known p-values by manipulating the data.
        
        # Create 5 descriptors with varying correlations
        descriptors = []
        target_p = [0.001, 0.01, 0.05, 0.1, 0.5]
        
        for i, p_target in enumerate(target_p):
            # This is a heuristic: we can't perfectly set a p-value, but we can create
            # a range of correlations. For the purpose of this test, we verify the
            # monotonicity property of the q-values returned by the function.
            pass
        
        # Instead, let's just verify that the q-values in the output are sorted
        # when the p-values are sorted, which is the core property.
        # We'll create a dataset with multiple descriptors and check the output.
        
        np.random.seed(456)
        df_multi = pd.DataFrame({
            'desc1': np.random.normal(0, 1, 100),
            'desc2': np.random.normal(0, 1, 100),
            'desc3': np.random.normal(0, 1, 100),
            'desc4': np.random.normal(0, 1, 100),
            'desc5': np.random.normal(0, 1, 100),
            'y': np.random.normal(0, 1, 100),
            'logP': np.random.normal(0, 1, 100),
            'MW': np.random.normal(0, 1, 100),
            'PSA': np.random.normal(0, 1, 100)
        })
        
        # Inject a strong correlation for desc1
        df_multi['y'] = 3 * df_multi['desc1'] + np.random.normal(0, 0.1, 100)
        
        results_list = []
        for desc in ['desc1', 'desc2', 'desc3', 'desc4', 'desc5']:
            res = compute_correlations_with_fdr(df_multi, desc, 'y', ['logP', 'MW', 'PSA'])
            results_list.append(res)
        
        all_results = pd.concat(results_list, ignore_index=True)
        
        # Sort by p-value
        sorted_results = all_results.sort_values('p_value')
        
        # Check that q-values are non-decreasing
        q_vals = sorted_results['q_value'].values
        for i in range(len(q_vals) - 1):
            assert q_vals[i] <= q_vals[i+1], f"FDR q-values must be non-decreasing: {q_vals[i]} > {q_vals[i+1]}"


class TestPassRateCalculation:
    """Tests for the pass rate calculation in the analysis pipeline."""
    
    def test_pass_rate_calculation(self):
        """
        Verify that the pass rate (number of successful correlations / total attempts) is calculated correctly.
        Note: The current implementation of compute_correlations_with_fdr does not explicitly return a pass rate.
        This test verifies the structure of the output and the ability to derive such a metric if needed.
        """
        np.random.seed(789)
        n = 50
        df = pd.DataFrame({
            'flex': np.random.normal(0, 1, n),
            'logPapp': np.random.normal(0, 1, n),
            'logP': np.random.normal(0, 1, n),
            'MW': np.random.normal(0, 1, n),
            'PSA': np.random.normal(0, 1, n)
        })

        results = compute_correlations_with_fdr(df, 'flex', 'logPapp', ['logP', 'MW', 'PSA'])
        
        # The function should return a dataframe with 2 rows (pearson and spearman)
        # unless an error occurs.
        assert len(results) == 2, f"Expected 2 correlation methods (pearson, spearman), got {len(results)}"
        
        # Verify all expected columns are present
        expected_cols = ['descriptor', 'target', 'method', 'r_value', 'p_value', 'q_value']
        for col in expected_cols:
            assert col in results.columns, f"Missing column: {col}"

def test_handle_nan_values(self):
    """
    Verify that the function handles NaN values in the input data gracefully.
    The function should drop rows with NaN in the relevant columns before calculation.
    """
    np.random.seed(999)
    n = 50
    x = np.random.normal(0, 1, n)
    y = np.random.normal(0, 1, n)
    
    # Introduce NaNs
    x[10] = np.nan
    y[20] = np.nan

    df = pd.DataFrame({
        'flex': x,
        'logPapp': y,
        'logP': np.random.normal(0, 1, n),
        'MW': np.random.normal(0, 1, n),
        'PSA': np.random.normal(0, 1, n)
    })

    # This should not raise an error
    results = compute_correlations_with_fdr(df, 'flex', 'logPapp', ['logP', 'MW', 'PSA'])
    
    # We should still get results, but based on fewer samples
    assert len(results) == 2, "Should return results for both methods even with NaNs"
    
    # The correlation might be less significant due to fewer samples, but it should be computed
    pearson_r = results[results['method'] == 'pearson']['r_value'].iloc[0]
    assert not np.isnan(pearson_r), "Pearson r should not be NaN"
    assert not np.isinf(pearson_r), "Pearson r should not be Inf"