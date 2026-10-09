"""
Zero-density sensitivity analysis for Möbius autocorrelation.

This script evaluates how sensitive the statistical significance (p-values)
of the observed autocorrelations is to small changes in the zero-density
of the Möbius function.

For each sampled window, it reruns the permutation test with the zero count
adjusted by ±5% and ±10%. If the significance (relative to alpha=0.05) 
changes for any perturbation, the lag is flagged as 'sensitive'.

The results are written back to ``data/processed/autocorr_stats.csv`` 
in a new column ``sensitivity_flag``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd

# Import the FFT-based autocorrelation helper from the public API
from autocorrelation import _compute_autocorrelation_all_fft

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
MOBIUS_PATH = Path("data/raw/mobius_array.npy")
WINDOW_STARTS_PATH = Path("data/raw/window_starts.json")
STATS_CSV = Path("data/processed/autocorr_stats.csv")

# Perturbation factors for zero density
DELTA_VALUES = [-0.10, -0.05, 0.05, 0.10]
# Reduced number of permutations for sensitivity to ensure timely execution
N_SENS_PERMUTATIONS = 100
BLOCK_SIZE = 100
RNG_SEED = 42
ALPHA = 0.05

def _ensure_parent_dir(p: Path) -> None:
    """Create the parent directory of ``p`` if it does not exist."""
    p.parent.mkdir(parents=True, exist_ok=True)

def _block_shuffle(window: np.ndarray, block_size: int, rng: np.random.Generator) -> np.ndarray:
    """Perform a block-permutation shuffle of the window."""
    # Split window into blocks
    blocks = [window[i : i + block_size] for i in range(0, len(window), block_size)]
    rng.shuffle(blocks)
    return np.concatenate(blocks)

def _compute_p_value(obs: float, null_vals: np.ndarray) -> float:
    """Two-sided p-value computation."""
    if np.isnan(obs):
        return float("nan")
    return np.mean(np.abs(null_vals) >= np.abs(obs))

def main() -> None:
    """
    Perform zero-density sensitivity analysis and update the stats CSV.
    """
    if not STATS_CSV.is_file():
        raise FileNotFoundError(f"Required stats CSV not found: {STATS_CSV}")
    if not MOBIUS_PATH.is_file():
        raise FileNotFoundError(f"Möbius array not found: {MOBIUS_PATH}")

    # Load data
    df = pd.read_csv(STATS_CSV)
    mobius = np.load(MOBIUS_PATH)
    with WINDOW_STARTS_PATH.open("r", encoding="utf-8") as f:
        window_map = json.load(f)

    # We will store flags in a dictionary keyed by (start, L, lag)
    # to map them back to the DataFrame rows.
    sensitivity_map = {}

    # To optimize, we process per unique window
    unique_windows = df[["interval_start", "interval_length"]].drop_duplicates()

    rng = np.random.default_rng(RNG_SEED)

    for _, row in unique_windows.iterrows():
        start = int(row["interval_start"])
        L = int(row["interval_length"])
        
        # Extract original window
        window = mobius[start : start + L]
        z_count = int(np.count_nonzero(window == 0))
        
        if z_count == L:
          # Window is all zeros; p-values are already NaN
          continue

        # Get the observed autocorrelations for this window for all lags
        # indices: 0 corresponds to lag 1, etc.
        observed_vals = _compute_autocorrelation_all_fft(mobius, start, L)
        
        # For each perturbation delta
        for delta in DELTA_VALUES:
            # Calculate perturbed zero count
            z_new = int(round(z_count * (1 + delta)))
            # Ensure z_new is within [0, L]
            z_new = max(0, min(L, z_new))
            
            # Create a perturbed window:
            # 1. Keep original non-zero signs, but sample to fit new count
            non_zeros = window[window != 0]
            nz_new_count = L - z_new
            
            if len(non_zeros) == 0:
                # If no non-zeros exist, we can't sample signs; skip
                continue
            
            sampled_nz = rng.choice(non_zeros, size=nz_new_count, replace=True)
            
            # 2. Combine zeros and sampled signs, then shuffle
            perturbed_base = np.concatenate([
                np.zeros(z_new, dtype=np.int8),
                sampled_nz
            ])
            rng.shuffle(perturbed_base)

            # 3. Generate null distribution via block permutations
            # We compute autocorrelation for each permuted sequence
            perm_ac_matrix = np.empty((N_SENS_PERMUTATIONS, len(observed_vals)), dtype=np.float64)
            for i in range(N_SENS_PERMUTATIONS):
                permuted_seq = _block_shuffle(perturbed_base, BLOCK_SIZE, rng)
                # Reuse FFT helper by creating a dummy full array
                dummy_full = np.concatenate(([0], permuted_seq))
                perm_ac_matrix[i] = _compute_autocorrelation_all_fft(dummy_full, 1, L)

            # 4. Compare p-values for each lag
            for lag_idx, obs_val in enumerate(observed_vals):
                lag = lag_idx + 1
                null_vals = perm_ac_matrix[:, lag_idx]
                p_new = _compute_p_value(obs_val, null_vals)
                
                # Retrieve baseline p-value from DataFrame
                # (Using a mask or index lookup)
                baseline_p = df[
                    (df["interval_start"] == start) & 
                    (df["interval_length"] == L) & 
                    (df["lag"] == lag)
                ]["p_value"].values[0]

                if np.isnan(baseline_p):
                    sensitivity_map[(start, L, lag)] = "not_applicable"
                    continue

                # Sensitivity check: Does significance cross the ALPHA threshold?
                sig_base = baseline_p < ALPHA
                sig_new = p_new < ALPHA
                
                if sig_base != sig_new:
                    sensitivity_map[(start, L, lag)] = "sensitive"
                elif (start, L, lag) not in sensitivity_map:
                    sensitivity_map[(start, L, lag)] = "stable"

    # Map flags back to the dataframe
    def get_flag(row):
        key = (int(row["interval_start"]), int(row["interval_length"]), int(row["lag"]))
        return sensitivity_map.get(key, "stable")

    df["sensitivity_flag"] = df.apply(get_flag, axis=1)

    # Save updated CSV
    _ensure_parent_dir(STATS_CSV)
    df.to_csv(STATS_CSV, index=False, float_format="%.12g")
    print(f"Sensitivity analysis completed. Updated {STATS_CSV}")

if __name__ == "__main__":
    main()