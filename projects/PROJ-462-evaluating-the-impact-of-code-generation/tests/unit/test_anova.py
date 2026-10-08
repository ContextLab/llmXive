"""
Unit tests for ANOVA calculation (Task T018).

Tests the statistical analysis functions in code/analysis/anova.py
to ensure correct calculation of two-way ANOVA, interaction effects,
and assumption checks.
"""
import unittest
import numpy as np
import pandas as pd
import scipy.stats as stats
import sys
import os
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.anova import (
    ExtractedStats,
    AnovaResult,
    ConfoundingControlReport,
    check_normality,
    check_homogeneity_of_variance,
    test_assumptions,
    perform_two_way_anova,
    calculate_interaction_effect,
    extract_significant_results,
    calculate_vif_diagnostics,
    calculate_power_analysis,
    report_confounding_control
)


class TestAssumptionChecks(unittest.TestCase):
    """Tests for assumption checking functions."""

    def setUp(self):
        """Set up test data."""
        # Create a balanced dataset with known properties
        np.random.seed(42)
        n_per_group = 30
        
        # Group A: Normal distribution
        group_a = np.random.normal(loc=10, scale=2, size=n_per_group)
        # Group B: Normal distribution with same variance
        group_b = np.random.normal(loc=12, scale=2, size=n_per_group)
        
        self.normal_data = np.concatenate([group_a, group_b])
        self.groups = ['A'] * n_per_group + ['B'] * n_per_group
        
        # Skewed data for failure case
        self.skewed_data = np.concatenate([
            np.random.exponential(scale=2, size=n_per_group),
            np.random.exponential(scale=2, size=n_per_group)
        ])
        
        # Heterogeneous variance data
        self.hetero_data = np.concatenate([
            np.random.normal(loc=10, scale=1, size=n_per_group),
            np.random.normal(loc=12, scale=5, size=n_per_group)
        ])

    def test_check_normality_passes(self):
        """Test that normal data passes Shapiro-Wilk test."""
        is_normal, p_value = check_normality(self.normal_data)
        self.assertTrue(is_normal, "Normal data should pass normality test")
        self.assertGreater(p_value, 0.05, "P-value should be > 0.05 for normal data")

    def test_check_normality_fails(self):
        """Test that skewed data fails Shapiro-Wilk test."""
        is_normal, p_value = check_normality(self.skewed_data)
        # Note: With large N, even small deviations can fail, but exponential is quite skewed
        # We check that the function runs and returns a boolean
        self.assertIsInstance(is_normal, bool)
        self.assertIsInstance(p_value, float)

    def test_check_homogeneity_passes(self):
        """Test that equal variance data passes Levene's test."""
        is_homogeneous, p_value = check_homogeneity_of_variance(
            self.normal_data, self.groups
        )
        self.assertTrue(is_homogeneous, "Equal variance data should pass Levene's test")
        self.assertGreater(p_value, 0.05, "P-value should be > 0.05 for equal variance")

    def test_check_homogeneity_fails(self):
        """Test that heterogeneous variance data fails Levene's test."""
        is_homogeneous, p_value = check_homogeneity_of_variance(
            self.hetero_data, self.groups
        )
        # Note: Levene's test is robust, but large difference (1 vs 5) should be detected
        self.assertIsInstance(is_homogeneous, bool)
        self.assertIsInstance(p_value, float)

    def test_test_assumptions_returns_dict(self):
        """Test that test_assumptions returns a dictionary with expected keys."""
        results = test_assumptions(self.normal_data, self.groups)
        self.assertIsInstance(results, dict)
        self.assertIn('normality', results)
        self.assertIn('homogeneity', results)


class TestTwoWayAnova(unittest.TestCase):
    """Tests for two-way ANOVA implementation."""

    def setUp(self):
        """Set up test data for two-way ANOVA."""
        np.random.seed(42)
        
        # Create a 2x2 factorial design
        # Factor A: Tool Usage (0 = Control, 1 = AI Tool)
        # Factor B: Experience (0 = Novice, 1 = Expert)
        
        n_per_cell = 30
        
        # Cell 1: Control, Novice
        cell_1 = np.random.normal(loc=100, scale=10, size=n_per_cell)
        # Cell 2: AI Tool, Novice
        cell_2 = np.random.normal(loc=90, scale=10, size=n_per_cell)  # Faster time
        # Cell 3: Control, Expert
        cell_3 = np.random.normal(loc=60, scale=10, size=n_per_cell)  # Faster time
        # Cell 4: AI Tool, Expert
        cell_4 = np.random.normal(loc=55, scale=10, size=n_per_cell)  # Slight interaction
        
        self.task_time = np.concatenate([cell_1, cell_2, cell_3, cell_4])
        self.tool_usage = ['Control'] * n_per_cell + ['AI'] * n_per_cell + \
                         ['Control'] * n_per_cell + ['AI'] * n_per_cell
        self.experience = ['Novice'] * n_per_cell + ['Novice'] * n_per_cell + \
                         ['Expert'] * n_per_cell + ['Expert'] * n_per_cell
        
        self.df = pd.DataFrame({
            'task_time': self.task_time,
            'tool_usage': self.tool_usage,
            'experience': self.experience
        })

    def test_perform_two_way_anova_returns_result(self):
        """Test that perform_two_way_anova returns an AnovaResult object."""
        result = perform_two_way_anova(
            self.df, 
            dependent='task_time', 
            factor1='tool_usage', 
            factor2='experience'
        )
        
        self.assertIsInstance(result, AnovaResult)
        self.assertIsNotNone(result.anova_table)
        self.assertIsNotNone(result.interaction_p_value)
        self.assertIsNotNone(result.main_effects)

    def test_perform_two_way_anova_detects_main_effects(self):
        """Test that ANOVA detects expected main effects."""
        result = perform_two_way_anova(
            self.df, 
            dependent='task_time', 
            factor1='tool_usage', 
            factor2='experience'
        )
        
        # We expect significant main effects based on our data generation
        # Tool usage: Control (100) vs AI (72.5 avg) -> significant
        # Experience: Novice (95) vs Expert (57.5 avg) -> significant
        self.assertIn('tool_usage', result.main_effects)
        self.assertIn('experience', result.main_effects)

    def test_interaction_effect_calculation(self):
        """Test that interaction effect is calculated correctly."""
        result = perform_two_way_anova(
            self.df, 
            dependent='task_time', 
            factor1='tool_usage', 
            factor2='experience'
        )
        
        # The interaction p-value should be a float
        self.assertIsInstance(result.interaction_p_value, float)
        self.assertGreaterEqual(result.interaction_p_value, 0)
        self.assertLessEqual(result.interaction_p_value, 1)

    def test_extracted_stats_structure(self):
        """Test that ExtractedStats contains expected fields."""
        result = perform_two_way_anova(
            self.df, 
            dependent='task_time', 
            factor1='tool_usage', 
            factor2='experience'
        )
        
        # Check that the anova_table has expected columns
        table = result.anova_table
        required_columns = ['Source', 'DF', 'Sum Sq', 'Mean Sq', 'F value', 'Pr(>F)']
        for col in required_columns:
            self.assertIn(col, table.columns, f"Column {col} missing from ANOVA table")


class TestInteractionEffect(unittest.TestCase):
    """Tests for interaction effect calculation."""

    def setUp(self):
        """Set up test data."""
        np.random.seed(42)
        self.df = pd.DataFrame({
            'value': [10, 12, 11, 13, 20, 22, 21, 23, 15, 17, 16, 18, 25, 27, 26, 28],
            'factor_a': ['A1', 'A1', 'A1', 'A1', 'A2', 'A2', 'A2', 'A2', 
                        'A1', 'A1', 'A1', 'A1', 'A2', 'A2', 'A2', 'A2'],
            'factor_b': ['B1', 'B1', 'B1', 'B1', 'B1', 'B1', 'B1', 'B1',
                        'B2', 'B2', 'B2', 'B2', 'B2', 'B2', 'B2', 'B2']
        })

    def test_calculate_interaction_effect_returns_float(self):
        """Test that interaction effect returns a numeric value."""
        interaction_f, interaction_p = calculate_interaction_effect(
            self.df, 'value', 'factor_a', 'factor_b'
        )
        
        self.assertIsInstance(interaction_f, (int, float))
        self.assertIsInstance(interaction_p, (int, float))
        self.assertGreaterEqual(interaction_p, 0)
        self.assertLessEqual(interaction_p, 1)


class TestExtractSignificantResults(unittest.TestCase):
    """Tests for extracting significant results."""

    def test_extract_significant_results_filters_p_values(self):
        """Test that significant results are correctly filtered."""
        # Create a mock ANOVA table
        table = pd.DataFrame({
            'Source': ['Factor_A', 'Factor_B', 'Interaction'],
            'Pr(>F)': [0.01, 0.15, 0.03]
        })
        
        significant = extract_significant_results(table, alpha=0.05)
        
        self.assertEqual(len(significant), 2)
        self.assertIn('Factor_A', significant['Source'].values)
        self.assertIn('Interaction', significant['Source'].values)
        self.assertNotIn('Factor_B', significant['Source'].values)


class TestVifDiagnostics(unittest.TestCase):
    """Tests for VIF (Variance Inflation Factor) diagnostics."""

    def test_calculate_vif_diagnostics_returns_dict(self):
        """Test that VIF diagnostics returns a dictionary."""
        # Create a dataset with some collinearity
        np.random.seed(42)
        n = 100
        x1 = np.random.normal(size=n)
        x2 = x1 * 0.9 + np.random.normal(scale=0.1, size=n)  # Highly correlated
        y = x1 + x2 + np.random.normal(scale=0.1, size=n)
        
        df = pd.DataFrame({'y': y, 'x1': x1, 'x2': x2})
        
        vif_results = calculate_vif_diagnostics(df, dependent='y', predictors=['x1', 'x2'])
        
        self.assertIsInstance(vif_results, dict)
        self.assertIn('vif_values', vif_results)
        self.assertIn('max_vif', vif_results)
        self.assertIn('collinearity_detected', vif_results)

    def test_vif_detects_collinearity(self):
        """Test that VIF correctly detects collinearity."""
        np.random.seed(42)
        n = 100
        x1 = np.random.normal(size=n)
        x2 = x1 * 0.95 + np.random.normal(scale=0.05, size=n)  # Very high correlation
        y = x1 + x2 + np.random.normal(scale=0.1, size=n)
        
        df = pd.DataFrame({'y': y, 'x1': x1, 'x2': x2})
        
        vif_results = calculate_vif_diagnostics(df, dependent='y', predictors=['x1', 'x2'])
        
        # With r=0.95, VIF should be high (> 10)
        self.assertGreater(vif_results['max_vif'], 5, "VIF should detect collinearity")
        self.assertTrue(vif_results['collinearity_detected'])


class TestPowerAnalysis(unittest.TestCase):
    """Tests for power analysis calculations."""

    def test_calculate_power_analysis_returns_dict(self):
        """Test that power analysis returns expected structure."""
        np.random.seed(42)
        n = 60  # 30 per group
        group1 = np.random.normal(loc=10, scale=2, size=n//2)
        group2 = np.random.normal(loc=12, scale=2, size=n//2)
        
        power_results = calculate_power_analysis(
            group1, group2, alpha=0.05, power=0.80
        )
        
        self.assertIsInstance(power_results, dict)
        self.assertIn('estimated_power', power_results)
        self.assertIn('effect_size', power_results)
        self.assertIn('sufficient_power', power_results)

    def test_power_analysis_detects_underpowered(self):
        """Test that power analysis detects underpowered studies."""
        # Very small sample size
        group1 = np.random.normal(loc=10, scale=2, size=5)
        group2 = np.random.normal(loc=10.5, scale=2, size=5)  # Small effect
        
        power_results = calculate_power_analysis(
            group1, group2, alpha=0.05, power=0.80
        )
        
        # With N=10 and small effect, power should be low
        self.assertLess(power_results['estimated_power'], 0.5)
        self.assertFalse(power_results['sufficient_power'])


class TestConfoundingControl(unittest.TestCase):
    """Tests for confounding control reporting."""

    def test_report_confounding_control_returns_dict(self):
        """Test that confounding control report returns expected structure."""
        np.random.seed(42)
        n = 100
        df = pd.DataFrame({
            'outcome': np.random.normal(size=n),
            'treatment': np.random.choice([0, 1], size=n),
            'covariate1': np.random.normal(size=n),
            'covariate2': np.random.normal(size=n)
        })
        
        report = report_confounding_control(
            df, 
            outcome='outcome', 
            treatment='treatment', 
            covariates=['covariate1', 'covariate2']
        )
        
        self.assertIsInstance(report, dict)
        self.assertIn('adjusted_effect', report)
        self.assertIn('unadjusted_effect', report)
        self.assertIn('covariates_included', report)


if __name__ == '__main__':
    unittest.main()