"""
Integration tests for FDR correction logic in correlation analysis.

This test verifies that:
1. The correlation results file exists and is readable.
2. The 'adj_p_value' column is present and correctly calculated.
3. All rows marked as 'significant' have an adjusted p-value < 0.05.
4. The FDR correction method used is Benjamini-Hochberg (verified by checking
   the monotonicity property of adjusted p-values when sorted by raw p-value).
"""
import pytest
import pandas as pd
import numpy as np
import os
import json
from pathlib import Path

# Ensure we can import from the code directory if needed, though we primarily
# test the output artifacts here.
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

def test_fdr_correction_logic():
    """
    Integration test for FDR correction logic.
    
    Verifies that the correlation analysis pipeline correctly applies
    Benjamini-Hochberg FDR correction and flags significant associations.
    """
    output_path = Path("data/processed/correlation_results.csv")
    
    if not output_path.exists():
        pytest.skip(
            f"Output not generated. Run code/03_correlation_analysis.py first. "
            f"Expected file: {output_path}"
        )
    
    try:
        df = pd.read_csv(output_path)
    except Exception as e:
        pytest.fail(f"Failed to read correlation results: {e}")
    
    # Verify required columns exist
    required_columns = ['genus', 'cognitive_metric', 'rho', 'p_value', 'adj_p_value', 'significant']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        pytest.fail(f"Missing required columns in output: {missing_cols}")
    
    # Verify adj_p_value is calculated (not all NaN or identical)
    if df['adj_p_value'].isna().all():
        pytest.fail("adj_p_value column is entirely NaN")
    
    # Verify significant flag logic: all significant rows must have adj_p < 0.05
    sig_df = df[df['significant'] == True]
    if len(sig_df) > 0:
        invalid_sig = sig_df[sig_df['adj_p_value'] >= 0.05]
        if not invalid_sig.empty:
            pytest.fail(
                f"Found {len(invalid_sig)} significant rows with adj_p_value >= 0.05. "
                f"Significance threshold is < 0.05."
            )
    
    # Verify Benjamini-Hochberg monotonicity property:
    # When sorted by raw p-value, adjusted p-values should be non-decreasing
    # (with minor floating point tolerance)
    if len(df) > 1:
        sorted_df = df.sort_values('p_value').reset_index(drop=True)
        adj_p = sorted_df['adj_p_value'].values
        
        # Check for non-decreasing order with tolerance
        non_decreasing = np.all(np.diff(adj_p) >= -1e-10)
        if not non_decreasing:
            # Log where the violation occurs for debugging
            violations = np.where(np.diff(adj_p) < -1e-10)[0]
            pytest.fail(
                f"Adj p-values violate BH monotonicity at indices {violations}. "
                f"This suggests incorrect FDR correction implementation."
            )
    
    # Verify that if there are significant results, the raw p-values are also
    # generally low (adj p < 0.05 implies raw p is typically < 0.05, though not always)
    if len(sig_df) > 0:
        # At least 90% of significant results should have raw p < 0.1
        low_raw_p_ratio = (sig_df['p_value'] < 0.1).mean()
        if low_raw_p_ratio < 0.9:
            pytest.fail(
                f"Only {low_raw_p_ratio:.1%} of significant results have raw p < 0.1. "
                f"This is unusually low and may indicate FDR correction issues."
            )

def test_fdr_correction_consistency_with_scipy():
    """
    Verify that our FDR correction matches scipy.stats multipletests.
    
    This test recalculates FDR correction on the raw p-values from the
    output file and compares with the stored adj_p_value.
    """
    output_path = Path("data/processed/correlation_results.csv")
    
    if not output_path.exists():
        pytest.skip("Output not generated. Run code/03_correlation_analysis.py first.")
    
    try:
        df = pd.read_csv(output_path)
    except Exception as e:
        pytest.fail(f"Failed to read correlation results: {e}")
    
    if 'p_value' not in df.columns or 'adj_p_value' not in df.columns:
        pytest.skip("Required p_value or adj_p_value columns missing.")
    
    from statsmodels.stats.multitest import multipletests
    
    raw_p_values = df['p_value'].dropna().values
    if len(raw_p_values) == 0:
        pytest.skip("No valid p-values to test.")
    
    # Apply BH FDR correction using statsmodels
    try:
        _, adj_p_values, _, _ = multipletests(raw_p_values, alpha=0.05, method='fdr_bh')
    except Exception as e:
        pytest.fail(f"Failed to compute FDR correction with statsmodels: {e}")
    
    # Compare with stored adjusted p-values (allowing for floating point differences)
    # We need to match them by row, so we sort both by p_value
    df_sorted = df.sort_values('p_value').reset_index(drop=True)
    stored_adj_p = df_sorted['adj_p_value'].values
    
    # Only compare rows where we have valid p-values
    valid_mask = ~np.isnan(raw_p_values)
    if not np.allclose(stored_adj_p[valid_mask], adj_p_values, rtol=1e-5, atol=1e-10):
        max_diff = np.max(np.abs(stored_adj_p[valid_mask] - adj_p_values))
        pytest.fail(
            f"Stored adj_p_values differ from statsmodels BH correction. "
            f"Max difference: {max_diff:.10f}. "
            f"Possible implementation error in apply_fdr_correction()."
        )

def test_fdr_correction_zero_p_values():
    """
    Test that FDR correction handles zero or very small p-values correctly.
    
    BH correction should not produce NaN or Inf for very small p-values.
    """
    output_path = Path("data/processed/correlation_results.csv")
    
    if not output_path.exists():
        pytest.skip("Output not generated. Run code/03_correlation_analysis.py first.")
    
    try:
        df = pd.read_csv(output_path)
    except Exception as e:
        pytest.fail(f"Failed to read correlation results: {e}")
    
    if 'adj_p_value' not in df.columns:
        pytest.skip("adj_p_value column missing.")
    
    # Check for NaN or Inf in adjusted p-values
    if df['adj_p_value'].isna().any():
        nan_count = df['adj_p_value'].isna().sum()
        pytest.fail(f"Found {nan_count} NaN values in adj_p_value column.")
    
    if np.isinf(df['adj_p_value']).any():
        inf_count = np.isinf(df['adj_p_value']).sum()
        pytest.fail(f"Found {inf_count} Inf values in adj_p_value column.")
    
    # All adjusted p-values should be between 0 and 1
    if (df['adj_p_value'] < 0).any() or (df['adj_p_value'] > 1).any():
        out_of_range = df[(df['adj_p_value'] < 0) | (df['adj_p_value'] > 1)]
        pytest.fail(
            f"Found {len(out_of_range)} adj_p_values outside [0, 1] range."
        )