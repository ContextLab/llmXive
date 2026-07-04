"""
Integration test for the preprocessing pipeline (User Story 1).

This test verifies that the full preprocessing pipeline:
1. Ingests synthetic data via MockAdapter
2. Filters by recovery time
3. Imputes missing values (half-min)
4. Applies TIC normalization and log transformation
5. Normalizes recovery metrics to RecoveryIndex
6. Outputs a valid DataFrame with correct schema and row counts
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np

# Ensure code/ is on path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from data.ingest import MockAdapter
from data.preprocess import (
    filter_by_recovery_time,
    impute_half_min,
    normalize_tic_and_log,
    normalize_recovery,
    check_missing_threshold
)
from utils.logging import get_logger, DataRejectionError

logger = get_logger(__name__)

@pytest.fixture
def synthetic_dataset():
    """Generate a real synthetic dataset using the MockAdapter."""
    adapter = MockAdapter()
    # Generate 100 samples with 'drought' stress type
    df = adapter.fetch(stress_type='drought', n_samples=100)
    return df

def test_pipeline_full_flow(synthetic_dataset):
    """
    End-to-end integration test for the preprocessing pipeline.
    
    Verifies:
    - No DataRejectionError is raised for valid data
    - Filtering reduces row count appropriately (if applicable)
    - Missing values are imputed correctly
    - Log transformation handles zeros
    - RecoveryIndex is normalized to [0, 1]
    - Output schema matches expectations
    """
    df = synthetic_dataset.copy()
    initial_rows = len(df)
    logger.info(f"Starting pipeline with {initial_rows} rows")

    # Step 1: Check missing threshold (should pass for synthetic data)
    try:
        check_missing_threshold(df, threshold=0.1)
        logger.info("Missing threshold check passed")
    except DataRejectionError as e:
        pytest.fail(f"Data rejected unexpectedly: {e}")

    # Step 2: Filter by recovery time (min 7 days)
    df_filtered = filter_by_recovery_time(df, min_days=7)
    logger.info(f"Filtered rows: {len(df_filtered)} (from {initial_rows})")
    
    # Synthetic data generator ensures most samples meet criteria, 
    # but we assert we have data remaining
    assert len(df_filtered) > 0, "Pipeline filtered out all data!"
    assert len(df_filtered) <= initial_rows

    # Step 3: Impute missing values with half-min
    df_imputed = impute_half_min(df_filtered)
    assert df_imputed.isnull().sum().sum() == 0, "Imputation failed: missing values remain"
    logger.info("Imputation complete: no missing values")

    # Step 4: Normalize TIC and apply log transformation
    df_processed = normalize_tic_and_log(df_imputed)
    
    # Verify log transformation: no negative values if input was positive
    # (log(0) is handled, but we check for NaNs introduced by log)
    assert not df_processed.isnull().any().any(), "Log transformation introduced NaNs"
    
    # Step 5: Normalize recovery metrics to RecoveryIndex (0-1)
    df_final = normalize_recovery(df_processed)
    
    # Verify RecoveryIndex exists and is in [0, 1]
    assert 'recovery_index' in df_final.columns, "RecoveryIndex column missing"
    ri = df_final['recovery_index']
    assert ri.min() >= 0 and ri.max() <= 1, f"RecoveryIndex out of bounds: [{ri.min()}, {ri.max()}]"
    
    logger.info(f"Pipeline complete. Final shape: {df_final.shape}")
    logger.info(f"RecoveryIndex range: [{ri.min():.4f}, {ri.max():.4f}]")

    # Final assertions on schema
    expected_columns = [
        'sample_id', 'stress_type', 'recovery_days', 'biomass_pre', 'biomass_post',
        'survival_pre', 'survival_post', 'recovery_index'
    ]
    # Check that key columns exist (may have more from metabolites)
    for col in ['sample_id', 'stress_type', 'recovery_index']:
        assert col in df_final.columns, f"Required column '{col}' missing"

def test_pipeline_handles_zeros_in_log(synthetic_dataset):
    """
    Specific test for FR-003: log transformation must handle zero values.
    """
    df = synthetic_dataset.copy()
    
    # Artificially introduce a zero in a metabolite column if possible
    # or rely on synthetic data generator not producing zeros (but we test robustness)
    # We'll force a zero in a numeric column to test the log logic
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        col = numeric_cols[0]
        df.loc[df.index[0], col] = 0.0
    
    # Run imputation (half-min might not catch 0 if min is 0, but log logic should)
    df_imputed = impute_half_min(df)
    df_processed = normalize_tic_and_log(df_imputed)
    
    # Should not crash and should not have NaN in that column
    assert not df_processed[col].isnull().any(), "Log transformation failed on zero value"

def test_pipeline_rejects_high_missing(synthetic_dataset):
    """
    Test that pipeline rejects data with >10% missing values.
    """
    df = synthetic_dataset.copy()
    
    # Introduce >10% missing in a critical column
    n_rows = len(df)
    n_missing = int(n_rows * 0.15)  # 15% missing
    df.loc[df.sample_id.head(n_missing).index, 'biomass_post'] = np.nan
    
    with pytest.raises(DataRejectionError):
        check_missing_threshold(df, threshold=0.1)