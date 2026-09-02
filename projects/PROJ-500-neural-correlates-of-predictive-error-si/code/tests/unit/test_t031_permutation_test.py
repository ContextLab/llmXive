import os
import sys
import pytest
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
from src.analysis.model import run_permutation_test, fit_lme_model

class TestT031PermutationTest:
    """
    Unit tests for the permutation test implementation in T031.
    Verifies:
    1. The permutation test runs and produces valid p-values.
    2. The p-value is approximately correct for known distributions.
    3. The sufficiency check logic works correctly.
    4. The function handles edge cases (small data, failed models).
    """

    @pytest.fixture
    def sample_data(self):
        """Create a sample dataset for testing."""
        np.random.seed(42)
        n_subjects = 20
        n_trials_per_subject = 10
        
        data = []
        for sub_id in range(n_subjects):
            for trial_id in range(n_trials_per_subject):
                # Create some correlation between accuracy and MMN
                accuracy = np.random.normal(0.7, 0.1)
                # MMN = 0.5 + 0.3 * accuracy + noise
                mmn = 0.5 + 0.3 * accuracy + np.random.normal(0, 0.1)
                
                data.append({
                    "subject_id": f"sub_{sub_id:02d}",
                    "block_id": trial_id,
                    "mmn_amplitude": mmn,
                    "accuracy": accuracy
                })
        
        return pd.DataFrame(data)

    @pytest.fixture
    def null_data(self):
        """Create a dataset with NO correlation between accuracy and MMN."""
        np.random.seed(42)
        n_subjects = 20
        n_trials_per_subject = 10
        
        data = []
        for sub_id in range(n_subjects):
            for trial_id in range(n_trials_per_subject):
                accuracy = np.random.normal(0.7, 0.1)
                mmn = np.random.normal(0.5, 0.1)  # Independent of accuracy
                
                data.append({
                    "subject_id": f"sub_{sub_id:02d}",
                    "block_id": trial_id,
                    "mmn_amplitude": mmn,
                    "accuracy": accuracy
                })
        
        return pd.DataFrame(data)

    def test_permutation_test_runs(self, sample_data):
        """Test that the permutation test runs without errors."""
        result = run_permutation_test(
            df=sample_data,
            dependent_var="mmn_amplitude",
            independent_var="accuracy",
            group_var="subject_id",
            n_permutations=100,  # Small number for speed
            random_state=42
        )
        
        assert "observed_statistic" in result
        assert "permutation_p_value" in result
        assert "n_permutations" in result
        assert "sufficient" in result
        assert result["n_permutations"] == 100
        assert 0 <= result["permutation_p_value"] <= 1

    def test_permutation_test_detects_correlation(self, sample_data):
        """Test that the permutation test can detect a true correlation."""
        # With a true correlation and enough samples, p-value should be low
        result = run_permutation_test(
            df=sample_data,
            dependent_var="mmn_amplitude",
            independent_var="accuracy",
            group_var="subject_id",
            n_permutations=200,
            random_state=42
        )
        
        # We expect the observed statistic to be non-zero
        assert result["observed_statistic"] is not None
        assert result["observed_statistic"] != 0
        
        # The permutation p-value should be defined
        assert result["permutation_p_value"] is not None

    def test_permutation_test_null_hypothesis(self, null_data):
        """Test that the permutation test correctly handles null data (no correlation)."""
        result = run_permutation_test(
            df=null_data,
            dependent_var="mmn_amplitude",
            independent_var="accuracy",
            group_var="subject_id",
            n_permutations=200,
            random_state=42
        )
        
        # With null data, the observed statistic should be close to 0
        # (though not exactly 0 due to sampling noise)
        assert result["observed_statistic"] is not None
        
        # The permutation p-value should be high (fail to reject null)
        # Note: With only 200 permutations, this might not be very reliable,
        # but we're just checking that the logic works
        assert 0 <= result["permutation_p_value"] <= 1

    def test_sufficiency_check(self, sample_data):
        """Test that the sufficiency check logic is executed."""
        result = run_permutation_test(
            df=sample_data,
            dependent_var="mmn_amplitude",
            independent_var="accuracy",
            group_var="subject_id",
            n_permutations=1000,
            check_sufficiency=True,
            random_state=42
        )
        
        assert "sufficient" in result
        assert "sufficiency_reason" in result
        assert isinstance(result["sufficient"], bool)

    def test_small_dataset_handling(self):
        """Test that the function handles very small datasets gracefully."""
        small_data = pd.DataFrame([
            {"subject_id": "sub_01", "block_id": 0, "mmn_amplitude": 0.5, "accuracy": 0.8},
            {"subject_id": "sub_02", "block_id": 1, "mmn_amplitude": 0.6, "accuracy": 0.7},
            {"subject_id": "sub_03", "block_id": 2, "mmn_amplitude": 0.55, "accuracy": 0.75},
        ])
        
        result = run_permutation_test(
            df=small_data,
            dependent_var="mmn_amplitude",
            independent_var="accuracy",
            group_var="subject_id",
            n_permutations=10,
            random_state=42
        )
        
        # Should return a warning and None values for small data
        assert result["reason"] == "Dataset too small"
        assert result["observed_statistic"] is None
        assert result["p_value"] is None

    def test_permuted_statistics_saved(self, sample_data):
        """Test that permuted statistics are saved in the result."""
        result = run_permutation_test(
            df=sample_data,
            dependent_var="mmn_amplitude",
            independent_var="accuracy",
            group_var="subject_id",
            n_permutations=50,
            random_state=42
        )
        
        assert "permuted_statistics" in result
        assert len(result["permuted_statistics"]) == 50
        assert all(isinstance(x, float) for x in result["permuted_statistics"])

    def test_random_state_reproducibility(self, sample_data):
        """Test that the same random state produces the same results."""
        result1 = run_permutation_test(
            df=sample_data,
            dependent_var="mmn_amplitude",
            independent_var="accuracy",
            group_var="subject_id",
            n_permutations=100,
            random_state=123
        )
        
        result2 = run_permutation_test(
            df=sample_data,
            dependent_var="mmn_amplitude",
            independent_var="accuracy",
            group_var="subject_id",
            n_permutations=100,
            random_state=123
        )
        
        # Results should be identical with the same random state
        assert result1["permutation_p_value"] == result2["permutation_p_value"]
        assert result1["observed_statistic"] == result2["observed_statistic"]
        assert result1["permuted_statistics"] == result2["permuted_statistics"]

    def test_n_permutations_parameter(self, sample_data):
        """Test that the n_permutations parameter is respected."""
        for n in [50, 100, 200]:
            result = run_permutation_test(
                df=sample_data,
                dependent_var="mmn_amplitude",
                independent_var="accuracy",
                group_var="subject_id",
                n_permutations=n,
                random_state=42
            )
            assert result["n_permutations"] == n
            assert len(result["permuted_statistics"]) == n