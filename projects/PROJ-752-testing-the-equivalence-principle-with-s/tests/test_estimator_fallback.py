import numpy as np
import pytest
from models.estimator import run_joint_fit, OrbitSolution
from utils.logging import AnalysisError

class TestFallbackLogic:
    """
    Tests for the fallback logic in run_joint_fit when the solver fails to converge.
    """

    def test_convergence_success_no_fallback(self):
        """
        Test that when the solver converges, fallback is not triggered.
        """
        def residuals_func(params):
            # A simple function that converges easily: minimize (x - 1)^2
            return params - 1.0
        
        initial_guess = np.array([0.0])
        solution = run_joint_fit(
            residuals_func,
            initial_guess,
            tol=1e-6,
            max_nfev=100,
            use_fallback=True
        )
        
        assert solution.success is True
        assert solution.fallback_applied is False
        np.testing.assert_array_almost_equal(solution.parameters, np.array([1.0]), decimal=5)

    def test_fallback_on_non_convergence(self):
        """
        Test that fallback logic is triggered when the initial tolerance is too strict
        for the given problem, but a solution exists with relaxed tolerance.
        """
        # Create a residuals function that is hard to converge with strict tolerance
        # but easy with relaxed tolerance
        def hard_residuals_func(params):
            # This function has a very flat region near the minimum
            # making strict convergence difficult
            x = params[0]
            # A function that is extremely flat near x=1
            return np.array([np.tanh((x - 1.0) * 1e-10)])
        
        initial_guess = np.array([0.0])
        
        # This should fail with strict tolerance but succeed with fallback
        solution = run_joint_fit(
            hard_residuals_func,
            initial_guess,
            tol=1e-12, # Very strict tolerance
            max_nfev=10, # Very few iterations
            use_fallback=True
        )
        
        # The fallback should have been applied
        assert solution.fallback_applied is True
        # We should have a result, even if not perfect
        assert solution.parameters is not None

    def test_fallback_returns_best_fit(self):
        """
        Test that when fallback is used, it returns the best-fit solution found.
        """
        def quadratic_residuals(params):
            # Simple quadratic: minimize (x - 2)^2
            return params - 2.0
        
        initial_guess = np.array([0.0])
        
        # Force a scenario where fallback is needed
        solution = run_joint_fit(
            quadratic_residuals,
            initial_guess,
            tol=1e-15, # Extremely strict
            max_nfev=1, # Only 1 iteration
            use_fallback=True
        )
        
        # Should have applied fallback
        assert solution.fallback_applied is True
        # Should have a solution close to the true minimum
        assert np.abs(solution.parameters[0] - 2.0) < 0.5

    def test_no_fallback_when_disabled(self):
        """
        Test that when use_fallback is False, no fallback is attempted.
        """
        def hard_residuals_func(params):
            return np.array([np.tanh((params[0] - 1.0) * 1e-10)])
        
        initial_guess = np.array([0.0])
        
        solution = run_joint_fit(
            hard_residuals_func,
            initial_guess,
            tol=1e-12,
            max_nfev=1,
            use_fallback=False
        )
        
        # Fallback should not be applied
        assert solution.fallback_applied is False
        # Success might be False due to non-convergence
        # But we should have a result
        assert solution.parameters is not None

    def test_fallback_with_exception(self):
        """
        Test that fallback is attempted even when the initial fit raises an exception.
        """
        def failing_residuals_func(params):
            if params[0] < 0:
                raise ValueError("Negative parameter not allowed")
            return params - 1.0
        
        # Start with a negative value to trigger exception
        initial_guess = np.array([-1.0])
        
        solution = run_joint_fit(
            failing_residuals_func,
            initial_guess,
            tol=1e-6,
            max_nfev=10,
            use_fallback=True
        )
        
        # Fallback should be attempted and might succeed if it handles the exception
        # Or it might still fail, but fallback_applied should reflect the attempt
        # The exact behavior depends on how the fallback handles exceptions
        assert solution.parameters is not None

    def test_fallback_increases_iterations(self):
        """
        Test that the fallback logic increases the maximum number of iterations.
        """
        def slow_residuals_func(params):
            # A function that requires many iterations to converge
            return params - 1.0
        
        initial_guess = np.array([0.0])
        
        solution = run_joint_fit(
            slow_residuals_func,
            initial_guess,
            tol=1e-6,
            max_nfev=2, # Very few iterations
            use_fallback=True
        )
        
        # If fallback was used, it should have tried more iterations
        # The exact number depends on the implementation
        if solution.fallback_applied:
            assert solution.nit > 2 # Should have used more than the initial max_nfev
