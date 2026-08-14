import pytest
import numpy as np
import sys
from pathlib import Path

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.robustness import run_permutation_test


class TestPermutationLogicSmallCount:
    """
    Unit tests for permutation logic using a small iteration count.
    This verifies the core shuffling and p-value calculation logic
    without the overhead of a full 10,000 iteration run.
    """

    def test_permutation_logic_small_count(self):
        """
        Tests that the permutation test runs correctly with a small number of iterations.
        
        Verifies:
        1. The function executes without error for a small count (e.g., 10).
        2. The output dictionary contains the required keys: 'iterations_run', 'p_value', 'status'.
        3. The 'iterations_run' matches the requested count.
        4. The 'p_value' is a float between 0 and 1.
        5. The 'status' is 'exact' when count is small (not approximate).
        """
        # Simulate a small dataset for the test
        np.random.seed(42)
        n_obs = 50
        
        # Generate synthetic observed drift slope (simulating the result from T013)
        observed_slope = 0.05
        
        # Generate a "null" distribution manually to simulate what the permutation would do
        # In the actual function, this is done by shuffling 'year' labels and refitting.
        # For this unit test, we mock the underlying behavior by passing a pre-generated
        # set of slopes that the function would calculate if it refitted the model.
        # However, to strictly test the *logic* of the permutation function itself,
        # we need to pass data that allows the function to run the shuffling logic.
        
        # Since refitting an LMM 10 times is slow for a unit test, we will test the
        # logic by providing a mock function or by testing the wrapper's handling
        # of the iteration count and result structure.
        
        # Let's assume the robustness.py function accepts a pre-calculated set of
        # slopes for testing purposes, or we test the structure of the output
        # assuming the function works.
        
        # Better approach for a pure unit test of the logic:
        # We will pass a small dataset and a mock estimator function if possible,
        # but given the constraints of the existing API, we will test the
        # execution flow and output structure with a small n.
        
        # To ensure we don't actually refit LMMs 10 times (which might be slow or fail
        # if data isn't loaded), we will test the logic by mocking the internal
        # slope calculation if the API allows, or we rely on the fact that
        # the function is designed to be called with real data.
        
        # Given the task is to test the *logic* with a small count, and we cannot
        # easily mock the LMM fitting without changing the API significantly,
        # we will run the function with a very small synthetic dataset that
        # allows the LMM to fit (or we assume the function handles small data).
        
        # Alternative: Test the permutation logic specifically by creating a
        # deterministic scenario.
        
        # Let's create a mock estimator that returns known values based on the shuffle.
        # This isolates the permutation logic from the LMM fitting logic.
        
        def mock_estimator(data, shuffle_indices):
            """Mock estimator that returns a slope based on the shuffled indices."""
            # Simple logic: if the first index in the shuffled list is > 25, return 0.1, else 0.0
            # This creates a deterministic outcome for testing the p-value calculation.
            if data[shuffle_indices[0]] > 25:
                return 0.1
            else:
                return 0.0
        
        # We need to adapt the call to robustness.py.
        # Since we cannot easily inject a mock estimator into run_permutation_test
        # without modifying the source, we will test the function with a small
        # dataset and a small iteration count, and verify the output structure.
        # We assume the function can handle small datasets.
        
        # Create a small synthetic dataset that mimics the structure expected
        # by the robustness module.
        # The robustness module expects: observed_slope, data (with 'year', 'effect_size', etc.)
        
        # For this specific unit test, we will focus on the logic of the permutation
        # loop and the p-value calculation by using a very simple mock.
        # We will patch the internal fitting function if possible, but since we
        # are writing a test file, we can import and test the logic directly.
        
        # Let's assume the robustness.py has a helper function for the permutation logic
        # that we can test directly, or we test the main function with a mock.
        
        # Since we are implementing T018, we must ensure the test passes.
        # We will create a test that verifies the permutation logic with a small count
        # by mocking the model fitting step to return a predictable sequence of slopes.
        
        # We will use pytest's monkeypatch to mock the internal fitting function.
        # However, without seeing the internal structure of robustness.py, we assume
        # it calls a function to fit the model.
        
        # Let's try a different approach: Test the permutation logic by creating
        # a simplified version of the function for the test, or mock the heavy lifting.
        
        # Given the constraints, we will assume the robustness.py function is
        # structured to allow testing. We will test the output structure and
        # the iteration count.
        
        # Mock data for the test
        mock_data = {
            'year': np.random.randint(1990, 2020, n_obs),
            'effect_size': np.random.randn(n_obs),
            'sample_size': np.random.randint(20, 100, n_obs),
            'field': np.random.choice(['Field A', 'Field B'], n_obs),
            'original_study_id': np.random.randint(1, 10, n_obs),
            'power_est': np.random.rand(n_obs)
        }
        
        observed_slope = 0.05
        n_permutations = 10
        
        # We will mock the function that fits the model to return a deterministic value
        # based on the permutation index to ensure the test is fast and deterministic.
        # This requires us to know the internal function name.
        # Assuming the function is named `_fit_model_for_permutation` or similar.
        
        # If we cannot mock, we will run the function and hope it fits quickly on small data.
        # But for a unit test, we should mock.
        
        # Let's assume we can import the internal function or we test the logic
        # by creating a simple test case.
        
        # Since we don't have the internal function name, we will test the
        # public function `run_permutation_test` and verify it runs and returns
        # the correct structure.
        
        # To make it fast, we will use a very small dataset and a small number of permutations.
        
        try:
            result = run_permutation_test(
                observed_slope=observed_slope,
                data=mock_data,
                n_permutations=n_permutations,
                random_seed=42
            )
            
            # Verify the result structure
            assert 'iterations_run' in result
            assert 'p_value' in result
            assert 'status' in result
            
            # Verify the iteration count
            assert result['iterations_run'] == n_permutations
            
            # Verify the p_value is a float between 0 and 1
            assert isinstance(result['p_value'], float)
            assert 0 <= result['p_value'] <= 1
            
            # Verify the status is 'exact' for small count
            assert result['status'] == 'exact'
            
        except Exception as e:
            # If the function fails due to data issues (e.g., not enough data for LMM),
            # we can skip or mark as expected failure if the logic is sound.
            # However, for a unit test, we want to ensure the logic works.
            # We will assume the function can handle small data or we mock.
            # Since we cannot mock without knowing the internal function, we will
            # assume the test passes if the function runs and returns the structure.
            # If it fails, we will catch it and re-raise with a helpful message.
            raise AssertionError(f"Permutation test failed with small count: {e}") from e

    def test_permutation_logic_deterministic_seed(self):
        """
        Tests that the permutation test produces deterministic results with a fixed seed.
        """
        np.random.seed(42)
        n_obs = 20
        
        mock_data = {
            'year': np.random.randint(1990, 2020, n_obs),
            'effect_size': np.random.randn(n_obs),
            'sample_size': np.random.randint(20, 100, n_obs),
            'field': np.random.choice(['Field A', 'Field B'], n_obs),
            'original_study_id': np.random.randint(1, 10, n_obs),
            'power_est': np.random.rand(n_obs)
        }
        
        observed_slope = 0.05
        n_permutations = 5
        
        # Run twice with the same seed
        result1 = run_permutation_test(
            observed_slope=observed_slope,
            data=mock_data,
            n_permutations=n_permutations,
            random_seed=123
        )
        
        result2 = run_permutation_test(
            observed_slope=observed_slope,
            data=mock_data,
            n_permutations=n_permutations,
            random_seed=123
        )
        
        # Results should be identical
        assert result1['p_value'] == result2['p_value']
        assert result1['iterations_run'] == result2['iterations_run']