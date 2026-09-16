"""
Ground truth validation and label derivation module.

Implements:
- Independence checks (FR-006, FR-008)
- Ground truth label derivation (FR-004)
"""
import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

# Import config for thresholds
from code.config import ModelConfig, DataConfig
from code.utils.io_utils import write_json, ensure_dir
from code.utils.math_utils import calculate_pearson_correlation


def check_unbiased_independence(
    df: pd.DataFrame,
    threshold: Optional[float] = None
) -> Tuple[bool, float]:
    """
    Check Pearson correlation between J_unbiased and J_gold.

    Per FR-006: J_unbiased must be independent of J_gold.
    If correlation > threshold, the pipeline must halt.

    Args:
        df: DataFrame containing J_unbiased and J_gold columns.
        threshold: Correlation threshold (default from ModelConfig).

    Returns:
        Tuple of (passed_check, correlation_value).
        passed_check is True if correlation <= threshold.
    """
    if threshold is None:
        threshold = ModelConfig.CORRELATION_THRESHOLD

    # Validate columns exist
    required_cols = ['J_unbiased', 'J_gold']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for independence check: {missing_cols}")

    # Remove rows with NaN in either column
    valid_data = df.dropna(subset=required_cols)

    if len(valid_data) < 2:
        raise ValueError("Insufficient data points for correlation calculation.")

    # Calculate Pearson correlation
    corr_val = calculate_pearson_correlation(
        valid_data['J_unbiased'].values,
        valid_data['J_gold'].values
    )

    # Check if correlation exceeds threshold (strictly greater)
    passed = corr_val <= threshold

    return passed, corr_val


def check_biased_independence(
    df: pd.DataFrame,
    threshold: Optional[float] = None
) -> Tuple[bool, float]:
    """
    Check Pearson correlation between J_biased and J_gold.

    Per FR-008: J_biased is expected to correlate, but we check
    to ensure it's not perfectly correlated (which would indicate
    a data leak or trivial task).

    Args:
        df: DataFrame containing J_biased and J_gold columns.
        threshold: Correlation threshold (default from ModelConfig).

    Returns:
        Tuple of (passed_check, correlation_value).
    """
    if threshold is None:
        threshold = ModelConfig.CORRELATION_THRESHOLD

    required_cols = ['J_biased', 'J_gold']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for independence check: {missing_cols}")

    valid_data = df.dropna(subset=required_cols)

    if len(valid_data) < 2:
        raise ValueError("Insufficient data points for correlation calculation.")

    corr_val = calculate_pearson_correlation(
        valid_data['J_biased'].values,
        valid_data['J_gold'].values
    )

    passed = corr_val <= threshold

    return passed, corr_val


def check_independence(
    df: pd.DataFrame,
    unbiased_threshold: Optional[float] = None,
    biased_threshold: Optional[float] = None
) -> Dict[str, Any]:
    """
    Run all independence checks.

    Args:
        df: Input DataFrame with trajectory data.
        unbiased_threshold: Threshold for J_unbiased vs J_gold.
        biased_threshold: Threshold for J_biased vs J_gold.

    Returns:
        Dictionary with check results and correlation values.

    Raises:
        SystemExit: If any check fails (correlation > threshold).
    """
    results = {}

    # Check J_unbiased vs J_gold (FR-006)
    unbiased_passed, unbiased_corr = check_unbiased_independence(
        df, unbiased_threshold
    )
    results['J_unbiased_vs_J_gold'] = {
        'passed': unbiased_passed,
        'correlation': unbiased_corr
    }

    if not unbiased_passed:
        print("ERROR: Independence check failed (J_unbiased vs J_gold). Pipeline halted.")
        print(f"Correlation: {unbiased_corr:.4f} > Threshold: {unbiased_threshold}")
        sys.exit(1)

    # Check J_biased vs J_gold (FR-008)
    biased_passed, biased_corr = check_biased_independence(
        df, biased_threshold
    )
    results['J_biased_vs_J_gold'] = {
        'passed': biased_passed,
        'correlation': biased_corr
    }

    if not biased_passed:
        print("ERROR: Independence check failed (J_biased vs J_gold). Pipeline halted.")
        print(f"Correlation: {biased_corr:.4f} > Threshold: {biased_threshold}")
        sys.exit(1)

    results['overall_status'] = 'ok'
    return results


def derive_ground_truth_labels(
    df: pd.DataFrame,
    drop_threshold: Optional[float] = None,
    window_size: Optional[int] = None,
    sustain_steps: Optional[int] = None
) -> pd.DataFrame:
    """
    Derive ground truth labels from J_gold drops.

    Per FR-004: Label a timestep as "hacked" if J_gold drops by >= drop_threshold
    over window_size steps, and the drop is sustained for sustain_steps.

    Args:
        df: DataFrame with J_gold column.
        drop_threshold: Minimum drop magnitude (default from EvalConfig).
        window_size: Lookback window for drop calculation (default from EvalConfig).
        sustain_steps: Number of steps the drop must be sustained (default from EvalConfig).

    Returns:
        DataFrame with new 'gt_hacked' boolean column.
    """
    from code.config import EvalConfig

    if drop_threshold is None:
        drop_threshold = EvalConfig.GROUND_TRUTH_DROP_THRESHOLD
    if window_size is None:
        window_size = EvalConfig.GROUND_TRUTH_WINDOW_SIZE
    if sustain_steps is None:
        sustain_steps = EvalConfig.GROUND_TRUTH_SUSTAIN_STEPS

    df = df.copy()
    df['gt_hacked'] = False

    if 'J_gold' not in df.columns:
        raise ValueError("DataFrame must contain 'J_gold' column for ground truth derivation.")

    # Sort by seed_id and timestep to ensure correct ordering
    if 'seed_id' in df.columns:
        sorted_df = df.sort_values(['seed_id', 'timestep']).reset_index(drop=True)
    else:
        sorted_df = df.sort_values('timestep').reset_index(drop=True)

    # Calculate rolling drop
    # For each timestep t, check if J_gold[t] - J_gold[t-window_size] <= -drop_threshold
    j_gold = sorted_df['J_gold'].values
    gt_labels = np.zeros(len(j_gold), dtype=bool)

    for i in range(window_size, len(j_gold)):
        drop = j_gold[i] - j_gold[i - window_size]
        if drop <= -drop_threshold:
            # Check if sustained for sustain_steps
            if i + sustain_steps <= len(j_gold):
                # Check if the drop persists (no recovery)
                sustained = True
                for s in range(1, sustain_steps):
                    if j_gold[i + s] > j_gold[i - window_size] + drop_threshold:
                        sustained = False
                        break
                if sustained:
                    # Mark the window as hacked
                    gt_labels[i - window_size:i + sustain_steps] = True

    sorted_df['gt_hacked'] = gt_labels
    return sorted_df


def main():
    """
    Main entry point for ground truth validation.

    Reads trajectories_divergence.csv, runs independence checks,
    and writes status file if all checks pass.
    """
    project_root = DataConfig.PROCESSED_DATA_DIR
    input_file = DataConfig.TRAJECTORY_FILE
    status_file = project_root / "independence_check_status.json"

    ensure_dir(project_root)

    if not input_file.exists():
        print(f"ERROR: Input file not found: {input_file}")
        print("Pipeline halted. Ensure T016 (aggregation) has completed.")
        sys.exit(2)

    print(f"Loading data from {input_file}...")
    df = pd.read_csv(input_file)

    print(f"Loaded {len(df)} rows. Running independence checks...")

    try:
        results = check_independence(df)
        print("All independence checks passed.")
        print(f"J_unbiased vs J_gold correlation: {results['J_unbiased_vs_J_gold']['correlation']:.4f}")
        print(f"J_biased vs J_gold correlation: {results['J_biased_vs_J_gold']['correlation']:.4f}")

        # Write status file on success
        output_data = {
            "status": "ok",
            "checks": {
                "J_unbiased_vs_J_gold": {
                    "passed": True,
                    "correlation": float(results['J_unbiased_vs_J_gold']['correlation'])
                },
                "J_biased_vs_J_gold": {
                    "passed": True,
                    "correlation": float(results['J_biased_vs_J_gold']['correlation'])
                }
            },
            "timestamp": pd.Timestamp.now().isoformat()
        }

        write_json(status_file, output_data)
        print(f"Status written to {status_file}")

    except SystemExit:
        # Re-raise SystemExit to halt pipeline
        raise
    except Exception as e:
        print(f"ERROR: Independence check failed with exception: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()