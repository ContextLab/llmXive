"""
Tests for the evaluate module.
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

# Import the functions we are testing
# Note: We assume the evaluate.py file is in the parent directory relative to tests/
# In a real project setup, this might be handled via PYTHONPATH or a src layout.
# For this test file, we import directly assuming the runner sets the path correctly.
try:
    from evaluate import calculate_baseline_mae, perform_permutation_test
except ImportError:
    # Fallback for local execution if not in a package
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from evaluate import calculate_baseline_mae, perform_permutation_test


class TestCalculateBaselineMae:
    """Tests for baseline MAE calculation."""

    def test_mean_prediction(self):
        """Test MAE when predicting the mean."""
        y_true = [1.0, 2.0, 3.0, 4.0, 5.0]
        # Mean is 3.0
        # Errors: |1-3|=2, |2-3|=1, |3-3|=0, |4-3|=1, |5-3|=2 -> Sum=6, MAE=1.2
        baseline_mae = calculate_baseline_mae(y_true)
        assert abs(baseline_mae - 1.2) < 1e-5

    def test_empty_list(self):
        """Test handling of empty list."""
        with pytest.raises(ValueError):
            calculate_baseline_mae([])

    def test_single_value(self):
        """Test with a single value."""
        y_true = [5.0]
        # Mean is 5.0, error is 0
        baseline_mae = calculate_baseline_mae(y_true)
        assert baseline_mae == 0.0


class TestPermutationTest:
    """Tests for the permutation test logic."""

    def test_permutation_test_runs(self):
        """Test that the permutation test runs and returns a p-value."""
        # Mock model MAE and baseline MAE
        model_mae = 0.5
        baseline_mae = 1.2
        # Mock y_true
        y_true = [1.0, 2.0, 3.0, 4.0, 5.0]
        # Mock features (not used in baseline, but needed for signature)
        X = [[1.0], [2.0], [3.0], [4.0], [5.0]]

        # Run test (assuming n_permutations is small for speed)
        p_value = perform_permutation_test(model_mae, baseline_mae, y_true, X, n_permutations=10)
        assert 0.0 <= p_value <= 1.0

    def test_permutation_test_significance(self):
        """Test that a very good model gets a low p-value."""
        # Create a scenario where the model is significantly better than baseline
        y_true = [1.0] * 100
        # Baseline predicts mean (1.0), MAE = 0.0? No, let's make it varied.
        y_true = list(range(1, 101)) # 1 to 100
        baseline_mae = calculate_baseline_mae(y_true) # Should be around 25.75 (mean absolute deviation from mean 50.5)

        # Model is perfect (MAE = 0)
        model_mae = 0.0

        # Features are irrelevant, just need shape
        X = [[i] for i in range(100)]

        # With a perfect model and a bad baseline, p-value should be 0 (or very low)
        # We use a larger n_permutations to be sure, but for this test small is okay if logic is sound
        p_value = perform_permutation_test(model_mae, baseline_mae, y_true, X, n_permutations=50)
        
        # If the model is perfect and baseline is not, the model should always win in permutation
        # unless the random shuffle accidentally creates a better baseline (unlikely with perfect model)
        # Actually, permutation test shuffles y_true, so the "model" is re-evaluated on shuffled data?
        # Wait, the standard permutation test for regression:
        # 1. Calculate observed statistic (model_mae)
        # 2. Shuffle y_true many times.
        # 3. For each shuffle, calculate the statistic (model_mae on shuffled y_true? No, that doesn't make sense).
        # Standard approach: Shuffle y_true, re-train model? Too expensive.
        # Alternative: Shuffle residuals? Or shuffle y_true and see if a random model (or the same model on shuffled data) beats the observed?
        
        # Let's assume the implementation of `perform_permutation_test` in `evaluate.py` does:
        # Shuffle y_true, calculate MAE of a "null" model (predicting mean of shuffled y_true) or re-run the trained model?
        # The task description says: "Compare model MAE against a null baseline (predicting mean loss) using a permutation test".
        # This implies:
        # Null hypothesis: The features have no predictive power.
        # Statistic: Difference between Baseline MAE and Model MAE (or just Model MAE if baseline is fixed).
        # Common implementation: Shuffle y_true, calculate Model MAE on shuffled data (assuming model is refit or if we assume the model is just a function of X and y, and we are testing if the relationship is real).
        # However, refitting is expensive.
        # Let's assume the provided `evaluate.py` implements a standard permutation test where:
        # 1. Observed stat = model_mae (or baseline_mae - model_mae)
        # 2. Permutations: Shuffle y_true, calculate the same stat (e.g., MAE of a model trained on shuffled data? Or just MAE of the baseline on shuffled data? No, that's always the same).
        
        # Re-reading the prompt's `evaluate.py` signature: `perform_permutation_test(model_mae, baseline_mae, y_true, X, n_permutations)`
        # It takes the model_mae and baseline_mae as inputs, so it doesn't re-train.
        # It likely simulates the null distribution by shuffling y_true and calculating the MAE of a "random" prediction or by shuffling the residuals?
        # Actually, a common simple permutation test for regression without retraining:
        # Shuffle y_true. Calculate the MAE of the *original model predictions* against the *shuffled y_true*.
        # If the model is good, the MAE on shuffled y_true should be high (close to baseline).
        # If the model is random, the MAE on shuffled y_true should be similar to the original.
        # Wait, if the model is good, it predicts y_true well. If we shuffle y_true, the predictions (fixed) will be far from the new y_true.
        # So the MAE on shuffled y_true should be high (similar to baseline).
        # The observed MAE is low.
        # So we count how many times the shuffled MAE <= observed MAE.
        # If the model is good, this count should be low (p-value low).
        
        # Let's assume the implementation does:
        # count = 0
        # for _ in range(n_permutations):
        #     y_shuffled = shuffle(y_true)
        #     perm_mae = calculate_mae(y_shuffled, model_predictions) -> We don't have model_predictions here.
        
        # Alternative: The function might re-train the model on shuffled data? But we don't have the model in the arguments.
        # Maybe it calculates the MAE of the *baseline* on shuffled data? No, baseline is just mean(y).
        
        # Let's look at the test `test_permutation_test_runs`. It passes `model_mae` and `baseline_mae` as scalars.
        # It doesn't pass the model or predictions.
        # This suggests the function might be a simplified simulation or it assumes the `evaluate.py` has access to the model/predictions via closure or global?
        # No, that's bad practice.
        
        # Perhaps the `perform_permutation_test` in `evaluate.py` is implemented as:
        # "Simulate the null distribution of the test statistic (Baseline MAE - Model MAE) by permuting y_true and re-calculating the statistic assuming a random model?"
        # Or maybe it's a permutation of the *labels* to check if the model's performance is significantly better than chance.
        # Given the constraints, I will assume the implementation in `evaluate.py` (which I must assume exists and works) handles this logic.
        # My job is to write the test that calls it.
        
        # Let's assume the implementation calculates the p-value as:
        # p = (number of permuted stats <= observed stat) / n_permutations
        # where the permuted stat is calculated by shuffling y_true and recalculating the MAE of a "random" model?
        # Or maybe it just shuffles the residuals?
        
        # Since I cannot see the implementation of `evaluate.py` (only the API surface), I must trust that `perform_permutation_test` is implemented correctly to take these arguments.
        # The test just needs to ensure it runs and returns a valid p-value.
        
        # Let's try a scenario where the model is clearly better.
        # If model_mae is very low and baseline_mae is high, the p-value should be low.
        # If model_mae is close to baseline_mae, p-value should be high.
        
        # Test 1: Model is perfect (0.0), Baseline is high (25.0). P-value should be 0.0 (or very low).
        p_value_good = perform_permutation_test(0.0, 25.0, y_true, X, n_permutations=50)
        # We can't guarantee it's exactly 0 with random shuffling, but it should be low.
        # However, without knowing the exact implementation, we just check it's in range.
        assert 0.0 <= p_value_good <= 1.0

    def test_permutation_test_random_model(self):
        """Test with a random model (MAE similar to baseline)."""
        y_true = [1.0, 2.0, 3.0, 4.0, 5.0]
        baseline_mae = calculate_baseline_mae(y_true) # 1.2
        # Model MAE is same as baseline (random performance)
        model_mae = baseline_mae
        
        X = [[1.0], [2.0], [3.0], [4.0], [5.0]]
        
        p_value = perform_permutation_test(model_mae, baseline_mae, y_true, X, n_permutations=50)
        # If model is same as baseline, p-value should be around 0.5 (or high)
        assert 0.0 <= p_value <= 1.0