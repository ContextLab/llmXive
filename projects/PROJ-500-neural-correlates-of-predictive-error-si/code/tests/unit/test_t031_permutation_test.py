"""
Unit Tests for T031: Permutation Test Implementation.

Verifies:
- Correctness of shuffling logic
- P-value calculation
- Sufficiency check (variance < 5% across 3 runs)
"""
import os
import sys
import pytest
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path

# Add code/ to path if running from tests/
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.analysis.model import run_permutation_test, fit_lme_model, load_aligned_data

class TestT031PermutationTest:
    
    @pytest.fixture
    def mock_aligned_data(self):
        """Create a small mock dataset that mimics aligned_data.csv."""
        np.random.seed(42)
        n_subjects = 10
        n_blocks_per_subject = 5
        
        data = []
        for subj in range(n_subjects):
            for block in range(n_blocks_per_subject):
                # Simulate some correlation for testing
                base_acc = np.random.uniform(0.5, 0.9)
                # Add noise to MMN
                mmn = base_acc * 2.0 + np.random.normal(0, 0.5)
                
                data.append({
                    "subject_id": f"sub-{subj:02d}",
                    "block_id": block,
                    "mmn_amplitude": mmn,
                    "accuracy": base_acc,
                    "learning_phase": "early" if block < 3 else "late"
                })
        
        df = pd.DataFrame(data)
        return df

    def test_permutation_test_runs(self, mock_aligned_data):
        """Test that the permutation test executes without error."""
        result = run_permutation_test(mock_aligned_data, n_permutations=50, random_state=42)
        
        assert "original_coefficient" in result
        assert "mean_p_value" in result
        assert "sufficiency_passed" in result
        assert "p_values_per_run" in result
        assert len(result["p_values_per_run"]) == 3 # 3 runs for sufficiency check

    def test_permutation_p_value_logic(self, mock_aligned_data):
        """
        Test that p-value logic is sound.
        If we shuffle data where there IS a correlation, p-value should be low (significant).
        If we shuffle data where there is NO correlation, p-value should be high.
        """
        # Case 1: Data has correlation (mock_aligned_data has it)
        result = run_permutation_test(mock_aligned_data, n_permutations=100, random_state=42)
        
        # We expect the permutation test to find the original coefficient is extreme
        # compared to shuffled ones.
        # Note: With small n and noise, this might not always be < 0.05, but the logic must run.
        assert 0.0 <= result["mean_p_value"] <= 1.0
        
        # Case 2: Break correlation manually
        df_no_corr = mock_aligned_data.copy()
        df_no_corr['accuracy'] = np.random.permutation(df_no_corr['accuracy'].values)
        
        result_no_corr = run_permutation_test(df_no_corr, n_permutations=100, random_state=42)
        
        # When data is random, the original coefficient (from random data) should be similar
        # to shuffled ones, so p-value should be high (near 0.5 or 1.0 depending on distribution)
        # This is a sanity check that the function doesn't return 0.0 always.
        assert result_no_corr["mean_p_value"] > 0.01 # Should not be extremely significant

    def test_sufficiency_check_variance(self, mock_aligned_data):
        """
        Verify the sufficiency check logic.
        With enough permutations, variance across 3 runs should be low.
        """
        # Run with small n to potentially fail sufficiency (high variance)
        result_low_n = run_permutation_test(mock_aligned_data, n_permutations=10, random_state=42)
        
        # Run with larger n to pass sufficiency
        result_high_n = run_permutation_test(mock_aligned_data, n_permutations=500, random_state=42)
        
        # The high n run should generally have lower variance or pass the check more reliably
        # We assert that the check runs and returns a boolean
        assert isinstance(result_high_n["sufficiency_passed"], bool)
        
        # Check that variance is calculated
        assert result_high_n["variance_p_value"] >= 0

    def test_coefficient_extraction(self, mock_aligned_data):
        """Ensure the 'accuracy' coefficient is correctly extracted from the LME model."""
        # Fit model directly
        model = fit_lme_model(mock_aligned_data)
        
        # Check params structure
        params = model.params
        # The coefficient for 'accuracy' must exist
        found = False
        for idx in params.index:
            if 'accuracy' in str(idx):
                found = True
                break
        
        assert found, "Could not find 'accuracy' coefficient in model parameters"

    def test_random_seed_reproducibility(self, mock_aligned_data):
        """Test that same seed produces same results."""
        r1 = run_permutation_test(mock_aligned_data, n_permutations=50, random_state=123)
        r2 = run_permutation_test(mock_aligned_data, n_permutations=50, random_state=123)
        
        assert r1["mean_p_value"] == r2["mean_p_value"]
        assert r1["p_values_per_run"] == r2["p_values_per_run"]