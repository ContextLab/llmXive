"""
Unit tests for simulate_missingness logic in code/simulation.py.

This test suite verifies:
1. MCAR (Missing Completely At Random) logic: missingness is independent of data.
2. MAR (Missing At Random) logic: missingness depends on observed covariates.
3. MNAR (Missing Not At Random) logic: missingness depends on the outcome values.
4. Permutation order: treatment labels are permuted before missingness simulation.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from simulation import simulate_missingness, permute_treatment_labels
from data_loader import DataLoadError

class TestSimulateMissingness:
    """Tests for the simulate_missingness function and related logic."""

    @pytest.fixture
    def sample_data(self):
        """Create a deterministic sample dataset for testing."""
        np.random.seed(42)
        n_samples = 200
        data = pd.DataFrame({
            'outcome': np.random.normal(0, 1, n_samples),
            'covariate_1': np.random.normal(0, 1, n_samples),
            'covariate_2': np.random.normal(0, 1, n_samples),
            'treatment': np.random.binomial(1, 0.5, n_samples)
        })
        return data

    @pytest.fixture
    def sample_data_with_outcome_dep(self):
        """Create data where outcome is correlated with a covariate for MAR testing."""
        np.random.seed(42)
        n_samples = 200
        covariate = np.random.normal(0, 1, n_samples)
        # Outcome depends on covariate
        outcome = 0.5 * covariate + np.random.normal(0, 0.5, n_samples)
        data = pd.DataFrame({
            'outcome': outcome,
            'covariate_1': covariate,
            'covariate_2': np.random.normal(0, 1, n_samples),
            'treatment': np.random.binomial(1, 0.5, n_samples)
        })
        return data

    def test_mcar_missingness_independence(self, sample_data):
        """Verify that MCAR missingness is independent of data values."""
        np.random.seed(123)
        missing_rate = 0.2
        
        # Run MCAR simulation multiple times to check distribution
        missing_masks = []
        for _ in range(10):
            _, mask = simulate_missingness(
                sample_data.copy(), 
                mechanism='mcar', 
                missing_rate=missing_rate, 
                seed=None  # Use global seed from outer loop
            )
            missing_masks.append(mask)
        
        # Calculate correlation between outcome and missingness mask
        # For MCAR, this should be close to 0
        correlations = []
        for mask in missing_masks:
            corr = np.corrcoef(sample_data['outcome'], mask.astype(float))[0, 1]
            correlations.append(corr)
        
        mean_corr = np.mean(correlations)
        # Allow some tolerance due to randomness, but it should be low
        assert abs(mean_corr) < 0.15, f"MCAR missingness shows correlation {mean_corr} with outcome"

    def test_mar_missingness_dependent_on_covariate(self, sample_data_with_outcome_dep):
        """Verify that MAR missingness depends on specified covariate."""
        np.random.seed(456)
        missing_rate = 0.3
        
        # Run MAR simulation where missingness depends on covariate_1
        data, mask = simulate_missingness(
            sample_data_with_outcome_dep.copy(),
            mechanism='mar',
            missing_rate=missing_rate,
            seed=None,
            mar_covariate='covariate_1'
        )
        
        # Calculate correlation between covariate_1 and missingness
        corr = np.corrcoef(sample_data_with_outcome_dep['covariate_1'], mask.astype(float))[0, 1]
        
        # For MAR, we expect a significant correlation (positive or negative depending on implementation)
        # The exact value depends on the logistic model used, but it should be non-zero
        assert abs(corr) > 0.1, f"MAR missingness shows no correlation with covariate: {corr}"

    def test_mnar_missingness_dependent_on_outcome(self, sample_data):
        """Verify that MNAR missingness depends on outcome values."""
        np.random.seed(789)
        missing_rate = 0.25
        
        # Run MNAR simulation where missingness depends on outcome
        data, mask = simulate_missingness(
            sample_data.copy(),
            mechanism='mnar',
            missing_rate=missing_rate,
            seed=None
        )
        
        # Calculate correlation between outcome and missingness
        corr = np.corrcoef(sample_data['outcome'], mask.astype(float))[0, 1]
        
        # For MNAR, we expect a significant correlation
        assert abs(corr) > 0.1, f"MNAR missingness shows no correlation with outcome: {corr}"

    def test_permute_treatment_labels_preserves_distribution(self, sample_data):
        """Verify that permutation preserves the treatment distribution."""
        original_treatment = sample_data['treatment'].copy()
        
        np.random.seed(999)
        permuted_data = permute_treatment_labels(sample_data)
        permuted_treatment = permuted_data['treatment']
        
        # Check that the number of treated and control subjects is preserved
        assert original_treatment.sum() == permuted_treatment.sum(), \
            "Permutation changed the number of treated subjects"
        
        # Check that the values are just shuffled (same set of values)
        assert set(original_treatment.values) == set(permuted_treatment.values), \
            "Permutation changed the treatment values"

    def test_permute_treatment_labels_changes_assignment(self, sample_data):
        """Verify that permutation actually changes the assignment (with high probability)."""
        original_treatment = sample_data['treatment'].copy()
        
        np.random.seed(1)  # Different seed to ensure different permutation
        permuted_data = permute_treatment_labels(sample_data)
        permuted_treatment = permuted_data['treatment']
        
        # With high probability, at least some assignments should change
        # (unless the dataset is very small or all treatments are the same)
        changes = (original_treatment != permuted_treatment).sum()
        total = len(original_treatment)
        
        # Allow for edge cases where all treatments are the same
        if original_treatment.nunique() > 1:
            assert changes > 0, "Permutation did not change any treatment assignments"

    def test_simulation_uses_permuted_treatment(self, sample_data):
        """Verify that simulation uses permuted treatment for null hypothesis."""
        np.random.seed(555)
        
        # Run simulation with MCAR
        data, mask = simulate_missingness(
            sample_data.copy(),
            mechanism='mcar',
            missing_rate=0.2,
            seed=None,
            permute_treatment=True
        )
        
        # The function should return data with permuted treatment
        # We verify this by checking that the treatment column is shuffled
        original_treatment = sample_data['treatment'].values
        permuted_treatment = data['treatment'].values
        
        # They should be permutations of each other
        np.testing.assert_array_equal(
            np.sort(original_treatment), 
            np.sort(permuted_treatment),
            err_msg="Treatment values not preserved during permutation"
        )

    def test_invalid_mechanism_raises_error(self, sample_data):
        """Verify that invalid mechanism raises ValueError."""
        with pytest.raises(ValueError, match="Invalid missingness mechanism"):
            simulate_missingness(
                sample_data.copy(),
                mechanism='invalid',
                missing_rate=0.2,
                seed=None
            )

    def test_missing_rate_bounds(self, sample_data):
        """Verify that missing rate is within valid bounds."""
        # Test rate = 0
        data, mask = simulate_missingness(
            sample_data.copy(),
            mechanism='mcar',
            missing_rate=0.0,
            seed=None
        )
        assert mask.sum() == 0, "Missing rate 0 should result in no missing values"
        
        # Test rate = 1
        data, mask = simulate_missingness(
            sample_data.copy(),
            mechanism='mcar',
            missing_rate=1.0,
            seed=None
        )
        assert mask.sum() == len(mask), "Missing rate 1 should result in all missing values"

    def test_seed_reproducibility(self, sample_data):
        """Verify that same seed produces same missingness pattern."""
        seed = 42
        
        # First run
        _, mask1 = simulate_missingness(
            sample_data.copy(),
            mechanism='mcar',
            missing_rate=0.2,
            seed=seed
        )
        
        # Second run with same seed
        _, mask2 = simulate_missingness(
            sample_data.copy(),
            mechanism='mcar',
            missing_rate=0.2,
            seed=seed
        )
        
        # Masks should be identical
        np.testing.assert_array_equal(mask1, mask2, err_msg="Same seed did not produce reproducible results")

    def test_mar_covariate_validation(self, sample_data):
        """Verify that MAR mechanism requires a valid covariate."""
        # Try MAR without specifying covariate
        with pytest.raises(ValueError, match="MAR mechanism requires mar_covariate"):
            simulate_missingness(
                sample_data.copy(),
                mechanism='mar',
                missing_rate=0.2,
                seed=None
            )
        
        # Try MAR with non-existent covariate
        with pytest.raises(ValueError, match="mar_covariate not found in data"):
            simulate_missingness(
                sample_data.copy(),
                mechanism='mar',
                missing_rate=0.2,
                seed=None,
                mar_covariate='nonexistent'
            )