import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from code.config import DataConfig, ModelConfig, EvalConfig, get_project_root
from code.utils.io_utils import load_csv, save_csv, ensure_dir
from code.utils.math_utils import safe_z_score
# Note: rolling_std_dev and handle_nan are not needed directly here;
# safe_z_score already handles epsilon flooring for zero variance.

# ----------------------------------------------------------------------
# Helper: compute sliding‑window z‑score for G(t) while excluding
# contaminated timesteps from the baseline statistics.
# ----------------------------------------------------------------------
def compute_z_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a column ``z_score_G`` to ``df`` containing the rolling
    z‑score of the divergence gap ``G_t``.

    The rolling window size ``W`` and the minimum number of samples
    are taken from :class:`DataConfig`.  Contaminated timesteps,
    indicated by the boolean column ``is_contaminated``, are ignored
    when computing the rolling mean and standard deviation.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame that must contain the columns:
        ``seed_id``, ``bias_type``, ``timestep``, ``G_t``,
        and ``is_contaminated``.

    Returns
    -------
    pd.DataFrame
        The original DataFrame with an added ``z_score_G`` column.
    """
    required = ['seed_id', 'bias_type', 'timestep', 'G_t', 'is_contaminated']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for z‑score computation: {missing}")

    # Configuration
    window = DataConfig.ROLLING_WINDOW_SIZE  # expected to be 20
    min_samples = DataConfig.MIN_ROLLING_SAMPLES  # expected to be 5

    # Work on a copy to avoid side‑effects
    result = df.copy()

    # Compute per‑seed & per‑bias rolling statistics
    group_keys = ['seed_id', 'bias_type']
    for _, group in result.groupby(group_keys):
        idx = group.index

        # Mask contaminated timesteps: they are excluded from the baseline
        clean_series = group['G_t'].mask(group['is_contaminated'])

        # Rolling mean / std on the *clean* series (NaNs are ignored)
        rolling_mean = clean_series.rolling(
            window=window, min_periods=min_samples
        ).mean()
        rolling_std = clean_series.rolling(
            window=window, min_periods=min_samples
        ).std(ddof=1)

        # Compute safe z‑score (handles zero std via epsilon floor)
        z = safe_z_score(group['G_t'], rolling_mean, rolling_std)

        # Assign back to the result DataFrame
        result.loc[idx, 'z_score_G'] = z

    return result

# ----------------------------------------------------------------------
# Existing utilities (unchanged apart from the integration of z‑score)
# ----------------------------------------------------------------------
def load_divergence_data() -> pd.DataFrame:
    """
    Loads the aggregated divergence data from T015/T016 output.
    Expects: data/processed/trajectories_divergence.csv
    """
    root = get_project_root()
    path = root / "data" / "processed" / "trajectories_divergence.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {path}. "
            "Please ensure T015 (aggregation) has completed successfully."
        )
    df = load_csv(str(path))

    # Validate required columns (allow missing z_score_G – it will be computed)
    required_cols = [
        'seed_id', 'bias_type', 'timestep',
        'G_t', 'dG_t', 'is_contaminated'
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Input data missing required columns: {missing}")

    return df

def calculate_dynamic_threshold(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculates dynamic thresholds for dG(t) based on the baseline noise.
    Uses the standard deviation of dG(t) excluding contaminated windows.
    Returns a dict with 'threshold_dG' and 'alpha_adjusted'.
    """
    # Filter out contaminated timesteps for baseline calculation
    clean_mask = ~df['is_contaminated']
    if clean_mask.sum() == 0:
        raise RuntimeError(
            "No clean timesteps available for baseline calculation. "
            "Contamination mask is all True."
        )

    clean_dG = df.loc[clean_mask, 'dG_t']

    # Baseline noise floor (global std of the clean dG)
    baseline_std = clean_dG.std()
    if pd.isna(baseline_std) or baseline_std == 0:
        baseline_std = 1e-6  # epsilon floor for zero variance

    # Bonferroni correction
    alpha_total = 0.05
    k = 3.0  # number of comparisons per FR‑003
    alpha_adj = alpha_total / k

    # Dynamic threshold for dG (one‑tailed, upper side)
    z_crit = stats.norm.ppf(1 - alpha_adj)
    threshold_dG = z_crit * baseline_std

    return {
        'threshold_dG': threshold_dG,
        'baseline_std': baseline_std,
        'alpha_adjusted': alpha_adj,
        'z_crit': z_crit,
    }

def apply_hacking_labels(df: pd.DataFrame, config: Dict[str, float]) -> pd.DataFrame:
    """
    Flags timesteps as 'hacked' if:
    1. p‑value(z_score_G) < alpha_adj
    OR
    2. p‑value(dG_t) < alpha_adj (i.e., dG_t > dynamic_threshold)

    The Bonferroni correction is applied to the alpha level used for
    these comparisons.
    """
    df = df.copy()

    alpha_adj = config['alpha_adjusted']
    threshold_dG = config['threshold_dG']

    # --- Z‑score condition -------------------------------------------------
    # One‑tailed test: larger G_t indicates hacking.
    df['p_value_z'] = 1 - stats.norm.cdf(df['z_score_G'])

    # --- ΔG condition ------------------------------------------------------
    clean_mask = ~df['is_contaminated']
    mean_dG = df.loc[clean_mask, 'dG_t'].mean()
    std_dG = config['baseline_std']

    # Z‑score for dG relative to clean baseline
    df['z_score_dG'] = (df['dG_t'] - mean_dG) / std_dG
    df['p_value_delta'] = 1 - stats.norm.cdf(df['z_score_dG'])

    # Apply Bonferroni‑adjusted significance threshold
    condition_z = df['p_value_z'] < alpha_adj
    condition_delta = df['p_value_delta'] < alpha_adj

    df['hacked_label'] = condition_z | condition_delta

    return df

def main():
    """
    Main entry point for T021/T022.
    1. Load divergence data.
    2. Compute sliding‑window z‑score (adds ``z_score_G``).
    3. Save the intermediate result (so downstream tasks see the column).
    4. Calculate dynamic thresholds and apply hacking labels (T022 logic).
    """
    print("Starting detector pipeline (z‑score computation + labeling)...")

    try:
        # Step 1: Load data
        df = load_divergence_data()

        # Step 2: Compute sliding‑window z‑score
        print("Computing sliding‑window z‑score (W=20, min 5 samples)...")
        df = compute_z_score(df)

        # Step 3: Persist the dataframe with the new ``z_score_G`` column.
        # This satisfies T021’s requirement to materialise the z‑score.
        root = get_project_root()
        interim_path = root / "data" / "processed" / "trajectories_divergence_z.csv"
        ensure_dir(interim_path)
        save_csv(df, str(interim_path))
        print(f"Saved intermediate file with z‑scores to: {interim_path}")

        # Step 4: Continue with dynamic‑threshold calculation and labeling
        # (the logic originally defined for T022).
        print("Calculating dynamic thresholds and applying hacking labels...")
        config = calculate_dynamic_threshold(df)
        df_labeled = apply_hacking_labels(df, config)

        # Step 5: Save final labeled output
        final_path = root / "data" / "processed" / "trajectories_divergence_labeled_temp.csv"
        ensure_dir(final_path)
        save_csv(df_labeled, str(final_path))
        print(f"Successfully saved labeled data to: {final_path}")

        total = len(df_labeled)
        hacked = df_labeled['hacked_label'].sum()
        print(f"Total timesteps: {total}")
        print(f"Hacked timesteps flagged: {hacked} ({100 * hacked / total:.2f}%)")

        return 0

    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1
    except ValueError as e:
        print(f"DATA ERROR: {e}")
        return 1
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())