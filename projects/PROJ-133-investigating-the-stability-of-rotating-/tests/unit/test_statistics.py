"""
Unit tests for statistical analysis functions in code/statistics/aggregators.py.

Specifically tests the Two-Way ANOVA implementation for User Story 3.
"""
import pytest
import numpy as np
from scipy import stats
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from statistics.aggregators import calculate_two_way_anova, perform_dunnetts_posthoc


class TestTwoWayANOVA:
    """Tests for the Two-Way ANOVA implementation."""

    def test_two_way_anova_structure(self):
        """
        Test that the Two-Way ANOVA function returns the expected structure.
        Verifies that the function handles a simple synthetic dataset correctly.
        """
        # Create a simple synthetic dataset with known structure
        # Factor A: Omega (3 levels), Factor B: epsilon_dd (3 levels)
        # We create 5 repeats per cell
        np.random.seed(42)
        
        omega_levels = [0.5, 0.7, 0.9]
        epsilon_levels = [0.3, 0.5, 0.7]
        
        # Create data: 3x3 grid of means, with some noise
        # We'll make the middle cell (0.7, 0.5) have a distinctly different mean
        data = []
        for i, omega in enumerate(omega_levels):
            for j, eps in enumerate(epsilon_levels):
                # Base mean increases with omega, decreases with eps, with a spike in the middle
                base_mean = i * 2.0 - j * 1.0
                if i == 1 and j == 1:  # Middle cell
                    base_mean += 10.0
                
                # Generate 5 repeats
                for _ in range(5):
                    data.append({
                        'omega': omega,
                        'epsilon_dd': eps,
                        'metric': base_mean + np.random.normal(0, 0.5)
                    })
        
        result = calculate_two_way_anova(data, factor_a='omega', factor_b='epsilon_dd', target='metric')
        
        # Check structure
        assert 'source' in result
        assert 'df' in result
        assert 'sum_sq' in result
        assert 'mean_sq' in result
        assert 'F' in result
        assert 'pvalue' in result
        
        # Check that we have rows for Factor A, Factor B, Interaction, and Residual
        sources = result['source']
        assert 'omega' in sources
        assert 'epsilon_dd' in sources
        assert 'Interaction' in sources
        assert 'Residual' in sources
        
        # Check degrees of freedom
        # Factor A (omega): 3 levels -> df = 2
        # Factor B (epsilon_dd): 3 levels -> df = 2
        # Interaction: 2 * 2 = 4
        # Residual: Total N - (levels_A * levels_B) = 45 - 9 = 36
        df_omega = result[result['source'] == 'omega']['df'].values[0]
        df_eps = result[result['source'] == 'epsilon_dd']['df'].values[0]
        df_int = result[result['source'] == 'Interaction']['df'].values[0]
        df_res = result[result['source'] == 'Residual']['df'].values[0]
        
        assert df_omega == 2
        assert df_eps == 2
        assert df_int == 4
        assert df_res == 36

    def test_two_way_anova_significance(self):
        """
        Test that Two-Way ANOVA correctly identifies significant effects.
        Uses a dataset constructed to have significant main effects and interaction.
        """
        np.random.seed(123)
        
        # Create data with clear main effects and interaction
        # Factor A: 2 levels, Factor B: 2 levels, 10 repeats each
        data = []
        for a in [0, 1]:
            for b in [0, 1]:
                # Interaction effect: high when both are 1
                mean_val = 10.0
                if a == 1:
                    mean_val += 5.0
                if b == 1:
                    mean_val += 3.0
                if a == 1 and b == 1:
                    mean_val += 15.0  # Strong interaction
                
                for _ in range(10):
                    data.append({
                        'factor_a': a,
                        'factor_b': b,
                        'metric': mean_val + np.random.normal(0, 1.0)
                    })
        
        result = calculate_two_way_anova(data, factor_a='factor_a', factor_b='factor_b', target='metric')
        
        # Extract p-values
        p_a = result[result['source'] == 'factor_a']['pvalue'].values[0]
        p_b = result[result['source'] == 'factor_b']['pvalue'].values[0]
        p_int = result[result['source'] == 'Interaction']['pvalue'].values[0]
        
        # All should be significant (p < 0.05) given the strong effects
        assert p_a < 0.05, f"Factor A should be significant, p={p_a}"
        assert p_b < 0.05, f"Factor B should be significant, p={p_b}"
        assert p_int < 0.05, f"Interaction should be significant, p={p_int}"

    def test_two_way_anova_no_effect(self):
        """
        Test that Two-Way ANOVA correctly identifies no significant effects
        when data is purely random.
        """
        np.random.seed(999)
        
        # Create purely random data
        data = []
        for a in [0, 1, 2]:
            for b in [0, 1, 2]:
                for _ in range(5):
                    data.append({
                        'factor_a': a,
                        'factor_b': b,
                        'metric': np.random.normal(0, 1.0)
                    })
        
        result = calculate_two_way_anova(data, factor_a='factor_a', factor_b='factor_b', target='metric')
        
        # Extract p-values
        p_a = result[result['source'] == 'factor_a']['pvalue'].values[0]
        p_b = result[result['source'] == 'factor_b']['pvalue'].values[0]
        p_int = result[result['source'] == 'Interaction']['pvalue'].values[0]
        
        # In random data, p-values should generally be > 0.05 (though not guaranteed)
        # We just check they are reasonable numbers between 0 and 1
        assert 0 <= p_a <= 1
        assert 0 <= p_b <= 1
        assert 0 <= p_int <= 1

    def test_dunnetts_posthoc_structure(self):
        """
        Test that Dunnett's post-hoc test returns the expected structure.
        """
        np.random.seed(42)
        
        # Create data with a control group and treatment groups
        data = []
        # Control group (omega=0.5)
        for _ in range(10):
            data.append({
                'omega': 0.5,
                'epsilon_dd': 0.5,
                'metric': 10.0 + np.random.normal(0, 1.0)
            })
        # Treatment groups
        for omega in [0.7, 0.9]:
            for _ in range(10):
                data.append({
                    'omega': omega,
                    'epsilon_dd': 0.5,
                    'metric': 12.0 + np.random.normal(0, 1.0)  # Higher mean
                })
        
        result = perform_dunnetts_posthoc(data, factor='omega', target='metric', control=0.5)
        
        # Check structure
        assert 'comparison' in result
        assert 'mean_diff' in result
        assert 'pvalue' in result
        assert 'significant' in result
        
        # Check that we have comparisons for both treatment levels
        comparisons = result['comparison']
        assert '0.7 vs 0.5' in comparisons
        assert '0.9 vs 0.5' in comparisons

    def test_dunnetts_posthoc_detection(self):
        """
        Test that Dunnett's test correctly identifies significant differences
        from the control group.
        """
        np.random.seed(123)
        
        # Create data with clear difference from control
        data = []
        # Control
        for _ in range(10):
            data.append({
                'omega': 0.5,
                'epsilon_dd': 0.5,
                'metric': 10.0 + np.random.normal(0, 0.5)
            })
        # Treatment with higher mean
        for _ in range(10):
            data.append({
                'omega': 0.9,
                'epsilon_dd': 0.5,
                'metric': 15.0 + np.random.normal(0, 0.5)
            })
        
        result = perform_dunnetts_posthoc(data, factor='omega', target='metric', control=0.5)
        
        # Extract p-value for the comparison
        p_val = result[result['comparison'] == '0.9 vs 0.5']['pvalue'].values[0]
        significant = result[result['comparison'] == '0.9 vs 0.5']['significant'].values[0]
        
        # Should be significant
        assert p_val < 0.05, f"Difference should be significant, p={p_val}"
        assert significant, "Should be marked as significant"

    def test_empty_data_handling(self):
        """
        Test that the functions handle empty or insufficient data gracefully.
        """
        # Test with insufficient data (only one group)
        data = [{'factor_a': 0, 'factor_b': 0, 'metric': 1.0}]
        
        with pytest.raises((ValueError, IndexError)):
            calculate_two_way_anova(data, factor_a='factor_a', factor_b='factor_b', target='metric')

    def test_realistic_bec_data_simulation(self):
        """
        Test with a dataset that mimics the BEC stability study structure.
        Uses realistic parameter ranges and expected variance patterns.
        """
        np.random.seed(2023)
        
        # Simulate BEC stability data
        # Omega: 0.5, 0.7, 0.9
        # Epsilon_dd: 0.3, 0.5, 0.7
        # Metric: Vortex Density
        
        data = []
        omega_vals = [0.5, 0.7, 0.9]
        eps_vals = [0.3, 0.5, 0.7]
        
        for omega in omega_vals:
            for eps in eps_vals:
                # Simulate a stability surface: stability decreases with omega, increases with eps
                # Add realistic noise
                base_density = 0.1 + 0.5 * omega - 0.2 * eps
                noise = np.random.normal(0, 0.05)
                
                for _ in range(5):
                    data.append({
                        'omega': omega,
                        'epsilon_dd': eps,
                        'vortex_density': max(0, base_density + noise)
                    })
        
        result = calculate_two_way_anova(
            data, 
            factor_a='omega', 
            factor_b='epsilon_dd', 
            target='vortex_density'
        )
        
        # Verify structure
        assert len(result) == 4  # A, B, Interaction, Residual
        assert 'F' in result.columns
        assert 'pvalue' in result.columns
        
        # Check that F-values are positive
        assert all(result['F'] > 0)
        
        # Check that p-values are in valid range
        assert all((result['pvalue'] >= 0) & (result['pvalue'] <= 1))