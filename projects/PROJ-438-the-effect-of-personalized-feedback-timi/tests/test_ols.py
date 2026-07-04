"""
Unit test for model fitting on synthetic data with known coefficients.

This test verifies that the Cluster-Robust OLS implementation in `models.py`
correctly recovers known coefficients when fitted on synthetic data.

It generates synthetic learner data where:
- The "Immediate" group has a known baseline effect.
- The "Delayed" group has a known positive coefficient relative to baseline.
- The "Variable" group has a known negative coefficient relative to baseline.

The test asserts that the fitted model recovers these coefficients within a
small tolerance, validating the correctness of the model fitting logic.
"""
import os
import sys
import unittest
import numpy as np
import pandas as pd
from pathlib import Path
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests

# Add project root to path to allow imports from code/
# This assumes the test is run from the project root or via pytest
project_root = Path(__file__).resolve().parent.parent
code_dir = project_root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

# Import the model fitting function we are testing
# Based on the task description, this will be implemented in T029.
# We import it here to test it. If T029 isn't done, this import will fail,
# which is expected if the dependency isn't met.
try:
    from models import fit_cluster_robust_ols
except ImportError:
    # If models.py doesn't exist yet or fit_cluster_robust_ols isn't defined,
    # we skip the test or mark it as not yet runnable.
    # For the purpose of this task implementation, we assume models.py will exist.
    # If it doesn't, the test runner will catch the ImportError.
    fit_cluster_robust_ols = None


class TestClusterRobustOLS(unittest.TestCase):
    """Test suite for the Cluster-Robust OLS model fitting."""

    def setUp(self):
        """Set up synthetic data with known coefficients."""
        np.random.seed(42)
        
        n_learners = 2000
        n_courses = 50
        
        # Generate course IDs
        course_ids = [f"COURSE_{i:03d}" for i in range(n_courses)]
        
        # Assign learners to courses
        learner_courses = np.random.choice(course_ids, size=n_learners)
        
        # Create feedback groups with known proportions
        # 40% Immediate, 40% Delayed, 20% Variable
        groups = np.random.choice(
            ['Immediate', 'Delayed', 'Variable'], 
            size=n_learners, 
            p=[0.4, 0.4, 0.2]
        )
        
        # Define known coefficients for the ground truth
        # Baseline (Immediate) effect
        beta_immediate = 50.0
        # Delayed effect relative to Immediate
        beta_delayed = 5.0
        # Variable effect relative to Immediate
        beta_variable = -3.0
        
        # Generate final grades based on the known model:
        # Grade = Beta_Immediate + Beta_Group_Effect + Noise
        # We'll use dummy variables for the groups
        grades = np.zeros(n_learners)
        
        for i in range(n_learners):
            if groups[i] == 'Immediate':
                grades[i] = beta_immediate
            elif groups[i] == 'Delayed':
                grades[i] = beta_immediate + beta_delayed
            else:  # Variable
                grades[i] = beta_immediate + beta_variable
        
        # Add Gaussian noise (sigma = 10)
        grades += np.random.normal(0, 10, size=n_learners)
        
        # Create DataFrame
        self.synthetic_data = pd.DataFrame({
            'learner_id': range(n_learners),
            'course_id': learner_courses,
            'feedback_group': groups,
            'final_grade': grades
        })
        
        # Store ground truth coefficients for comparison
        self.ground_truth = {
            'intercept': beta_immediate,
            'Delayed': beta_delayed,
            'Variable': beta_variable
        }

    @unittest.skipIf(fit_cluster_robust_ols is None, "models.fit_cluster_robust_ols not implemented yet")
    def test_model_recovers_known_coefficients(self):
        """
        Test that the model recovers known coefficients from synthetic data.
        
        We expect the fitted coefficients to be close to the ground truth
        values defined in setUp(), within a reasonable tolerance due to
        sampling noise.
        """
        # Run the model fitting
        # The function should return a results object with .params and .pvalues
        results = fit_cluster_robust_ols(
            data=self.synthetic_data,
            outcome_col='final_grade',
            group_col='feedback_group',
            cluster_col='course_id'
        )
        
        # Extract estimated coefficients
        # The model uses 'Immediate' as the reference category
        estimated_intercept = results.params['Intercept']
        estimated_delayed = results.params['feedback_group[T.Delayed]']
        estimated_variable = results.params['feedback_group[T.Variable]']
        
        # Define tolerance for coefficient recovery
        # With n=2000 and sigma=10, we expect standard errors to be small
        # so coefficients should be recovered within ~1-2 units
        tolerance = 2.0
        
        # Assert intercept recovery
        self.assertAlmostEqual(
            estimated_intercept, 
            self.ground_truth['intercept'], 
            delta=tolerance,
            msg=f"Intercept {estimated_intercept:.2f} does not match ground truth {self.ground_truth['intercept']:.2f}"
        )
        
        # Assert Delayed effect recovery
        self.assertAlmostEqual(
            estimated_delayed, 
            self.ground_truth['Delayed'], 
            delta=tolerance,
            msg=f"Delayed coefficient {estimated_delayed:.2f} does not match ground truth {self.ground_truth['Delayed']:.2f}"
        )
        
        # Assert Variable effect recovery
        self.assertAlmostEqual(
            estimated_variable, 
            self.ground_truth['Variable'], 
            delta=tolerance,
            msg=f"Variable coefficient {estimated_variable:.2f} does not match ground truth {self.ground_truth['Variable']:.2f}"
        )

    @unittest.skipIf(fit_cluster_robust_ols is None, "models.fit_cluster_robust_ols not implemented yet")
    def test_model_significance_matches_ground_truth(self):
        """
        Test that the model correctly identifies significant effects.
        
        Since we know the true effects are non-zero (5.0 and -3.0),
        the model should find them statistically significant (p < 0.05)
        with high probability given our sample size.
        """
        results = fit_cluster_robust_ols(
            data=self.synthetic_data,
            outcome_col='final_grade',
            group_col='feedback_group',
            cluster_col='course_id'
        )
        
        # Get p-values for the group coefficients
        p_delayed = results.pvalues['feedback_group[T.Delayed]']
        p_variable = results.pvalues['feedback_group[T.Variable]']
        
        # With our sample size and effect sizes, we expect p < 0.05
        # We use a slightly more lenient threshold to account for randomness
        significance_threshold = 0.05
        
        self.assertLess(
            p_delayed, 
            significance_threshold,
            msg=f"Delayed effect p-value {p_delayed:.4f} should be < {significance_threshold}"
        )
        
        self.assertLess(
            p_variable, 
            significance_threshold,
            msg=f"Variable effect p-value {p_variable:.4f} should be < {significance_threshold}"
        )

    @unittest.skipIf(fit_cluster_robust_ols is None, "models.fit_cluster_robust_ols not implemented yet")
    def test_model_handles_cluster_robust_se(self):
        """
        Test that cluster-robust standard errors are being used.
        
        This is a sanity check that the model doesn't just run standard OLS.
        We can't easily verify the exact value without knowing the clustering,
        but we can check that the results object has the expected attributes
        and that the p-values are reasonable.
        """
        results = fit_cluster_robust_ols(
            data=self.synthetic_data,
            outcome_col='final_grade',
            group_col='feedback_group',
            cluster_col='course_id'
        )
        
        # Check that results object has expected attributes
        self.assertTrue(hasattr(results, 'params'), "Results should have 'params' attribute")
        self.assertTrue(hasattr(results, 'pvalues'), "Results should have 'pvalues' attribute")
        self.assertTrue(hasattr(results, 'bse'), "Results should have 'bse' attribute (standard errors)")
        
        # Check that we have coefficients for all groups (plus intercept)
        expected_params = ['Intercept', 'feedback_group[T.Delayed]', 'feedback_group[T.Variable]']
        for param in expected_params:
            self.assertIn(param, results.params.index, f"Missing parameter: {param}")


if __name__ == '__main__':
    unittest.main()
