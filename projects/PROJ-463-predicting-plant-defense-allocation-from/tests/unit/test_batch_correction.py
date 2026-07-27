"""
Unit tests for batch correction module.
"""
import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from src.data.batch_correction import calculate_cv_reduction, apply_batch_correction
from src.utils.config import set_seed

@pytest.fixture
def mock_tpm_matrix():
    """Create a mock TPM matrix with known batch effects."""
    set_seed(42)
    # Create a matrix with 10 genes and 10 samples
    # 5 samples in Batch A, 5 in Batch B
    # Add a systematic shift for Batch B to simulate batch effect
    genes = [f"Gene{i}" for i in range(10)]
    samples_a = [f"SampleA{i}" for i in range(5)]
    samples_b = [f"SampleB{i}" for i in range(5)]
    all_samples = samples_a + samples_b

    data = np.random.lognormal(mean=0, sigma=1, size=(10, 10))
    df = pd.DataFrame(data, index=genes, columns=all_samples)

    # Add batch effect: multiply Batch B values by 2
    for col in samples_b:
        df[col] = df[col] * 2

    return df, {**{s: "A" for s in samples_a}, **{s: "B" for s in samples_b}}

def test_cv_reduction_calculation(mock_tpm_matrix):
    """Test that CV reduction is calculated correctly."""
    tpm_df, sample_batches = mock_tpm_matrix

    # Calculate CV reduction
    pre_cv, post_cv, reduction = calculate_cv_reduction(tpm_df, sample_batches=sample_batches)

    # Pre-correction CV should be higher than post-correction CV due to batch effect removal
    assert pre_cv > post_cv, "Pre-correction CV should be higher than post-correction CV"
    assert reduction > 0, "Reduction should be positive"
    assert isinstance(pre_cv, float)
    assert isinstance(post_cv, float)
    assert isinstance(reduction, float)

def test_batch_correction_logic(mock_tpm_matrix):
    """Test that batch correction actually reduces variance."""
    tpm_df, sample_batches = mock_tpm_matrix

    # Apply correction
    corrected_df = apply_batch_correction(tpm_df, sample_batches)

    # Check that the corrected values are closer to the global mean
    # For Batch B, the values were multiplied by 2, so correction should bring them back down
    for gene in tpm_df.index:
        original_batch_b_mean = tpm_df.loc[gene, [s for s in tpm_df.columns if s.startswith("SampleB")]].mean()
        corrected_batch_b_mean = corrected_df.loc[gene, [s for s in corrected_df.columns if s.startswith("SampleB")]].mean()
        global_mean = tpm_df.loc[gene].mean()

        # The corrected mean should be closer to the global mean than the original mean
        assert abs(corrected_batch_b_mean - global_mean) < abs(original_batch_b_mean - global_mean), \
            f"Correction failed for {gene}: {corrected_batch_b_mean} vs {global_mean}"