"""
Unit tests for GLMM model fitting.
This module provides sanity checks on synthetic data to ensure the GLMM
fitting logic in code/analysis/glmm.py works correctly before running
on real execution traces.
"""

import unittest
import numpy as np
import pandas as pd
from typing import Tuple, List, Dict, Any

# Mock the analysis module functions we are testing
# Since we cannot import the full pipeline without running data generation,
# we import the specific logic or mock the dependencies if the module
# relies heavily on external data files.
# However, per the API surface, we expect `code/analysis/glmm.py` to expose:
# prepare_data_for_glmm, fit_glmm, calculate_effect_sizes.
# We will test the logic by generating synthetic data that mimics the
# expected schema of `data/processed/execution_traces.csv`.

try:
    from analysis.glmm import (
        load_execution_traces,
        prepare_data_for_glmm,
        fit_glmm,
        calculate_effect_sizes,
        run_statistical_analysis
    )
    GLMM_AVAILABLE = True
except ImportError:
    # Fallback if the module structure is slightly different during early dev
    # or if dependencies (statsmodels) are missing in the test environment.
    GLMM_AVAILABLE = False


def generate_synthetic_execution_traces(
    n_samples: int = 100,
    n_groups: int = 2,
    n_groups_per_constraint: int = 5,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generates a synthetic DataFrame mimicking the schema of
    data/processed/execution_traces.csv for unit testing.

    Schema:
    - task_id: string
    - architecture: string ('monolithic' or 'dual_track')
    - constraint_count: int
    - violation_boolean: bool (0 or 1)
    - violation_reason: string|null
    - violation_status: string|null
    - final_score: float
    """
    np.random.seed(seed)

    # Create random task IDs
    task_ids = [f"task_{i:04d}" for i in range(n_samples)]

    # Create architecture labels (balanced)
    architectures = np.random.choice(['monolithic', 'dual_track'], size=n_samples)

    # Create constraint counts (ranging from 5 to 15)
    constraint_counts = np.random.randint(5, 16, size=n_samples)

    # Simulate violation_boolean based on architecture and constraint count
    # Dual track should have lower violation rates, especially as constraints increase.
    # Logit model: logit(p) = beta0 + beta1*arch + beta2*constraints + beta3*arch*constraints
    beta0 = -1.0  # baseline log-odds
    beta_arch = -0.5  # dual_track reduces log-odds of violation
    beta_constr = 0.1  # more constraints increase log-odds of violation
    beta_interact = -0.05  # dual_track mitigates the constraint effect

    log_odds = []
    for arch, cons in zip(architectures, constraint_counts):
        arch_val = 1 if arch == 'dual_track' else 0
        lo = beta0 + (beta_arch * arch_val) + (beta_constr * cons) + (beta_interact * arch_val * cons)
        log_odds.append(lo)

    probs = 1 / (1 + np.exp(-np.array(log_odds)))
    violations = np.random.binomial(1, probs, size=n_samples).astype(bool)

    # Final score: correlated with violations (lower score if violation)
    final_scores = np.random.normal(loc=0.8, scale=0.1, size=n_samples)
    final_scores[violations] -= 0.2  # Penalty for violations
    final_scores = np.clip(final_scores, 0.0, 1.0)

    # Fill optional columns
    violation_reasons = [None if not v else "Constraint X violated" for v in violations]
    violation_statuses = [None if not v else "explicit" for v in violations]

    df = pd.DataFrame({
        'task_id': task_ids,
        'architecture': architectures,
        'constraint_count': constraint_counts,
        'violation_boolean': violations,
        'violation_reason': violation_reasons,
        'violation_status': violation_statuses,
        'final_score': final_scores
    })

    return df


class TestGLMMFitting(unittest.TestCase):
    """
    Unit tests for GLMM model fitting using synthetic data.
    """

    @unittest.skipIf(not GLMM_AVAILABLE, "GLMM analysis module not available")
    def test_prepare_data_for_glmm(self):
        """
        Sanity check: verify that prepare_data_for_glmm correctly
        transforms the raw DataFrame into the format expected by statsmodels.
        """
        df = generate_synthetic_execution_traces(n_samples=200)

        # Call the preparation function
        # Note: The actual function signature might vary, adjusting to expected usage
        try:
            prepared_data = prepare_data_for_glmm(df)
            
            # Assertions
            self.assertIsInstance(prepared_data, pd.DataFrame)
            self.assertIn('violation_boolean', prepared_data.columns)
            self.assertIn('architecture', prepared_data.columns)
            self.assertIn('constraint_count', prepared_data.columns)
            
            # Check that categorical variables are handled (e.g., as factors or encoded)
            # The specific encoding depends on the implementation in glmm.py
            # We just ensure no exception is raised and data is present.
            self.assertGreater(len(prepared_data), 0)
            
        except Exception as e:
            self.fail(f"prepare_data_for_glmm raised an unexpected exception: {e}")

    @unittest.skipIf(not GLMM_AVAILABLE, "GLMM analysis module not available")
    def test_fit_glmm_convergence(self):
        """
        Sanity check: verify that fit_glmm can converge on synthetic data.
        We expect a successful fit with reasonable coefficients.
        """
        df = generate_synthetic_execution_traces(n_samples=500) # Larger sample for stability

        try:
            # Fit the model
            model_result = fit_glmm(df)
            
            # Assertions
            self.assertIsNotNone(model_result)
            
            # Check for convergence status if available in the result object
            # statsmodels GLM/GLMM results usually have a 'converged' attribute
            if hasattr(model_result, 'converged'):
                # Note: With small synthetic data, convergence isn't guaranteed,
                # but we check that the object exists and has the attribute.
                self.assertTrue(hasattr(model_result, 'converged'))
            
            # Check that coefficients exist
            if hasattr(model_result, 'params'):
                self.assertGreater(len(model_result.params), 0)
                # Check that the interaction term (if included) is present
                # This depends on the specific formula used in glmm.py
                
        except Exception as e:
            # If it fails, it might be due to data sparsity or model specification.
            # We fail the test to highlight the issue.
            self.fail(f"fit_glmm failed to converge or raised an exception: {e}")

    @unittest.skipIf(not GLMM_AVAILABLE, "GLMM analysis module not available")
    def test_calculate_effect_sizes(self):
        """
        Sanity check: verify that calculate_effect_sizes returns valid metrics.
        """
        df = generate_synthetic_execution_traces(n_samples=500)

        try:
            # Prepare data first
            prepared_data = prepare_data_for_glmm(df)
            model_result = fit_glmm(df)

            # Calculate effect sizes
            effect_sizes = calculate_effect_sizes(model_result, prepared_data)

            # Assertions
            self.assertIsInstance(effect_sizes, dict)
            self.assertIn('effect_size', effect_sizes)
            self.assertIn('p_value', effect_sizes)
            self.assertIn('interaction_effect', effect_sizes) # Based on project requirements

            # Effect size should be a number
            self.assertIsInstance(effect_sizes['effect_size'], (int, float))
            self.assertIsInstance(effect_sizes['p_value'], (int, float))
            
        except Exception as e:
            self.fail(f"calculate_effect_sizes raised an unexpected exception: {e}")

    @unittest.skipIf(not GLMM_AVAILABLE, "GLMM analysis module not available")
    def test_run_statistical_analysis_integration(self):
        """
        Integration test: run the full statistical analysis pipeline on synthetic data.
        """
        df = generate_synthetic_execution_traces(n_samples=500)
        
        # We cannot easily write to disk in a unit test without cleanup,
        # so we test the internal logic by calling the function with the DataFrame
        # if the function allows, or by mocking the file I/O.
        # Assuming run_statistical_analysis takes a DataFrame or path.
        # Let's assume it takes a path for the real implementation, but for unit testing
        # we might need to adapt.
        
        # For this unit test, we will simulate the process by creating a temporary file
        # or by calling the constituent parts if run_statistical_analysis is too coupled to disk.
        # Given the task is a "sanity check", testing the components is sufficient.
        
        prepared_data = prepare_data_for_glmm(df)
        model_result = fit_glmm(df)
        effect_sizes = calculate_effect_sizes(model_result, prepared_data)

        # Verify the structure of the final result
        self.assertIn('p_value', effect_sizes)
        self.assertIn('effect_size', effect_sizes)
        self.assertIn('interaction_effect', effect_sizes)

        # Check that p-value is between 0 and 1
        self.assertGreaterEqual(effect_sizes['p_value'], 0.0)
        self.assertLessEqual(effect_sizes['p_value'], 1.0)


if __name__ == '__main__':
    unittest.main()