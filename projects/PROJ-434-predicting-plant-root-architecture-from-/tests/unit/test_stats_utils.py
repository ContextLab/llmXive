import pytest
import numpy as np
from numpy.testing import assert_array_almost_equal
from code.utils.stats import calculate_metrics, calculate_baseline_r2, delta_r2, permutation_test, stratified_permutation_test
from code.utils.exceptions import DataQualityError

class TestCalculateMetrics:
    def test_calculate_metrics_basic(self):
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.1, 2.1, 2.9, 4.2, 4.8])
        
        r2, rmse = calculate_metrics(y_true, y_pred)
        
        assert 0.9 < r2 < 1.0
        assert rmse < 0.2

    def test_calculate_metrics_perfect_prediction(self):
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.0, 2.0, 3.0])
        
        r2, rmse = calculate_metrics(y_true, y_pred)
        
        assert r2 == 1.0
        assert rmse == 0.0

    def test_calculate_metrics_empty_arrays(self):
        with pytest.raises(ValueError):
            calculate_metrics(np.array([]), np.array([]))

    def test_calculate_metrics_shape_mismatch(self):
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.0, 2.0])
        
        with pytest.raises(ValueError):
            calculate_metrics(y_true, y_pred)

class TestCalculateBaselineR2:
    def test_calculate_baseline_r2(self):
        y_train = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_test = np.array([2.0, 3.0, 4.0])
        
        baseline_r2 = calculate_baseline_r2(y_train, y_test)
        
        assert -1.0 <= baseline_r2 <= 1.0

    def test_calculate_baseline_r2_constant_train(self):
        y_train = np.array([5.0, 5.0, 5.0])
        y_test = np.array([5.0, 5.0, 5.0])
        
        baseline_r2 = calculate_baseline_r2(y_train, y_test)
        
        assert baseline_r2 == 0.0 or baseline_r2 == 1.0

class TestDeltaR2:
    def test_delta_r2_positive(self):
        observed_r2 = 0.8
        baseline_r2 = 0.5
        
        result = delta_r2(observed_r2, baseline_r2)
        
        assert result == 0.3

    def test_delta_r2_negative(self):
        observed_r2 = 0.4
        baseline_r2 = 0.6
        
        result = delta_r2(observed_r2, baseline_r2)
        
        assert result == -0.2

class TestPermutationTest:
    def test_permutation_test_basic(self):
        np.random.seed(42)
        X = np.random.randn(50, 3)
        y = np.random.randn(50)
        
        r2_scores = permutation_test(
            X, y, 
            n_permutations=10, 
            random_state=42,
            model_type='rf'
        )
        
        assert len(r2_scores) == 10
        assert all(isinstance(score, float) for score in r2_scores)

    def test_permutation_test_single_iteration(self):
        np.random.seed(42)
        X = np.random.randn(20, 2)
        y = np.random.randn(20)
        
        r2_scores = permutation_test(
            X, y, 
            n_permutations=1, 
            random_state=42,
            model_type='rf'
        )
        
        assert len(r2_scores) == 1

    def test_permutation_test_zero_iterations(self):
        with pytest.raises(ValueError):
            permutation_test(
                np.array([]), np.array([]), 
                n_permutations=0, 
                random_state=42,
                model_type='rf'
            )

class TestStratifiedPermutationTest:
    def test_stratified_permutation_test_basic(self):
        np.random.seed(42)
        n_samples = 100
        X = np.random.randn(n_samples, 3)
        y = np.random.randn(n_samples)
        # Create stratified groups (e.g., species)
        species = np.repeat(['A', 'B', 'C', 'D', 'E'], 20)
        
        r2_scores = stratified_permutation_test(
            X, y, species,
            n_permutations=10, 
            random_state=42,
            model_type='rf'
        )
        
        assert len(r2_scores) == 10
        assert all(isinstance(score, float) for score in r2_scores)

    def test_stratified_permutation_test_single_group(self):
        np.random.seed(42)
        X = np.random.randn(20, 2)
        y = np.random.randn(20)
        species = np.array(['A'] * 20)
        
        r2_scores = stratified_permutation_test(
            X, y, species,
            n_permutations=5, 
            random_state=42,
            model_type='rf'
        )
        
        assert len(r2_scores) == 5

    def test_stratified_permutation_test_imbalanced_groups(self):
        np.random.seed(42)
        X = np.random.randn(50, 2)
        y = np.random.randn(50)
        species = np.array(['A'] * 10 + ['B'] * 40)
        
        r2_scores = stratified_permutation_test(
            X, y, species,
            n_permutations=5, 
            random_state=42,
            model_type='rf'
        )
        
        assert len(r2_scores) == 5

class TestIntegration:
    def test_full_pipeline_scenario(self):
        """Test a scenario combining multiple functions."""
        np.random.seed(42)
        
        # Generate synthetic data
        X = np.random.randn(100, 4)
        y = 2 * X[:, 0] + 0.5 * X[:, 1] + np.random.randn(100) * 0.1
        y_train, y_test = y[:80], y[80:]
        
        # Calculate baseline
        baseline_r2 = calculate_baseline_r2(y_train, y_test)
        
        # Simulate observed R2 (higher than baseline)
        observed_r2 = 0.85
        
        # Calculate delta
        d_r2 = delta_r2(observed_r2, baseline_r2)
        
        assert d_r2 > 0
        assert -1.0 <= baseline_r2 <= 1.0
        assert -1.0 <= observed_r2 <= 1.0
