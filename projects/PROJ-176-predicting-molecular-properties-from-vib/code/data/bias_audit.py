"""
bias_audit.py
----------------
Selection‑bias audit for the aligned QM9 + IR‑spectra dataset.

This script performs a two‑sample Kolmogorov–Smirnov (KS) test for each
target property (dipole moment, polarizability, HOMO‑LUMO gap) comparing
the distribution in the *aligned* subset against the distribution in the
*full* QM9 dataset.  The KS statistics and p‑values are stored in the
``selection_bias_stats`` field of ``data/processed/aligned_dataset.npz``.

If any property shows a statistically significant bias (p < 0.05) the
script additionally computes inverse‑probability weights for each aligned
sample using kernel‑density estimates (KDE) of the full and aligned
distributions and saves the resulting weight mask to
``data/processed/weight_mask.npy``.
"""

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Constants – imported from the preprocessing module to guarantee column‑name
# handling and unit conversion consistency.
# ----------------------------------------------------------------------
from data.preprocess import (
    DIPOLE_COLS,
    POLARIZABILITY_COLS,
    GAP_COLS,
    BOHR3_TO_ANGSTROM3,
    HARTREE_TO_EV,
)

LOG = get_logger(__name__)


def _select_column(df: pd.DataFrame, candidates: list) -> str | None:
    """Return the first column name from *candidates* that exists in *df*."""
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _load_full_qm9() -> pd.DataFrame:
    """Load the full QM9 dataset (properties only)."""
    qm9_path = Path("data/raw/qm9.parquet")
    if not qm9_path.is_file():
        raise FileNotFoundError(f"Full QM9 file not found: {qm9_path}")
    LOG.info("Loading full QM9 dataset from %s", qm9_path)
    return pd.read_parquet(qm9_path, engine="pyarrow")


def _convert_properties(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert raw QM9 columns to the canonical units used downstream:
    - dipole   : Debye (already in Debye for the canonical column)
    - polarizability : Bohr³ → Å³
    - gap      : Hartree → eV
    """
    # Dipole
    dip_col = _select_column(df, DIPOLE_COLS)
    if dip_col is None:
        raise KeyError(f"Unable to locate dipole column. Expected one of {DIPOLE_COLS}")
    df["dipole"] = df[dip_col].astype(float)

    # Polarizability
    pol_col = _select_column(df, POLARIZABILITY_COLS)
    if pol_col is None:
        raise KeyError(
            f"Unable to locate polarizability column. Expected one of {POLARIZABILITY_COLS}"
        )
    df["polarizability"] = df[pol_col].astype(float) * BOHR3_TO_ANGSTROM3

    # HOMO‑LUMO gap
    gap_col = _select_column(df, GAP_COLS)
    if gap_col is None:
        raise KeyError(f"Unable to locate gap column. Expected one of {GAP_COLS}")
    df["gap"] = df[gap_col].astype(float) * HARTREE_TO_EV

    return df


def _load_aligned_npz() -> dict:
    """Load the aligned NPZ file produced by ``code/data/preprocess.py``."""
    npz_path = paths.data("processed", "aligned_dataset.npz")
    if not npz_path.is_file():
        raise FileNotFoundError(f"Aligned dataset not found: {npz_path}")
    LOG.info("Loading aligned dataset from %s", npz_path)
    # ``allow_pickle=True`` is required because we store a dict in the file.
    return np.load(npz_path, allow_pickle=True)


def _ks_test(full_vals: np.ndarray, aligned_vals: np.ndarray) -> dict:
    """Run a two‑sample KS test and return ``statistic`` and ``p_value``."""
    statistic, p_value = stats.ks_2samp(full_vals, aligned_vals)
    return {"statistic": float(statistic), "p_value": float(p_value)}


def _compute_weights(
    full_vals: np.ndarray, aligned_vals: np.ndarray, eps: float = 1e-12
) -> np.ndarray:
    """
    Compute inverse‑probability weights for a single property using KDE.

    ``weight_i = pdf_full(x_i) / (pdf_aligned(x_i) + eps)``

    The function returns a 1‑D array of weights with the same length as
    ``aligned_vals``.
    """
    # Fit KDEs; ``bw_method='scott'`` gives a reasonable bandwidth for 1‑D data.
    kde_full = stats.gaussian_kde(full_vals, bw_method="scott")
    kde_aligned = stats.gaussian_kde(aligned_vals, bw_method="scott")

    pdf_full = kde_full.evaluate(aligned_vals)
    pdf_aligned = kde_aligned.evaluate(aligned_vals)

    # Guard against division by zero.
    weights = pdf_full / (pdf_aligned + eps)
    # Normalise to have mean 1.0 (optional but makes downstream usage easier).
    weights /= np.mean(weights)
    return weights.astype(np.float32)


def main() -> None:
    """
    Entry point for the bias‑audit script.

    Steps:
    1. Load the full QM9 dataset and convert to canonical units.
    2. Load the aligned NPZ file and extract target arrays.
    3. Perform KS tests for each property.
    4. Write the KS results back into the NPZ under ``selection_bias_stats``.
    5. If any p‑value < 0.05, compute inverse‑probability weights and
       save ``weight_mask.npy``.
    """
    LOG.info("Starting selection‑bias audit")

    # ------------------------------------------------------------------
    # 1. Load full QM9 and convert units
    # ------------------------------------------------------------------
    full_qm9_df = _load_full_qm9()
    full_qm9_df = _convert_properties(full_qm9_df)

    # ------------------------------------------------------------------
    # 2. Load aligned data
    # ------------------------------------------------------------------
    aligned_data = _load_aligned_npz()
    dip_aligned = aligned_data["dipole"]
    pol_aligned = aligned_data["polarizability"]
    gap_aligned = aligned_data["gap"]

    # ------------------------------------------------------------------
    # 3. KS tests
    # ------------------------------------------------------------------
    ks_results = {}
    for name, full_arr, aligned_arr in [
        ("dipole", full_qm9_df["dipole"].to_numpy(), dip_aligned),
        ("polarizability", full_qm9_df["polarizability"].to_numpy(), pol_aligned),
        ("gap", full_qm9_df["gap"].to_numpy(), gap_aligned),
    ]:
        result = _ks_test(full_arr, aligned_arr)
        ks_results[name] = result
        LOG.info(
            "KS test for %s – statistic: %.5f, p‑value: %.5f",
            name,
            result["statistic"],
            result["p_value"],
        )

    # ------------------------------------------------------------------
    # 4. Write back to the NPZ
    # ------------------------------------------------------------------
    # Preserve all existing arrays (including any previous placeholder dict)
    npz_path = paths.data("processed", "aligned_dataset.npz")
    npz_path.parent.mkdir(parents=True, exist_ok=True)

    # Gather all arrays from the original file (except the old dict)
    preserved = {
        key: aligned_data[key]
        for key in aligned_data.files
        if key != "selection_bias_stats"
    }

    # Add the new stats dict
    preserved["selection_bias_stats"] = ks_results

    # Overwrite the NPZ with the updated contents
    np.savez_compressed(npz_path, **preserved)
    LOG.info("Updated aligned_dataset.npz with selection‑bias statistics")

    # ------------------------------------------------------------------
    # 5. Optional weighting
    # ------------------------------------------------------------------
    any_bias = any(res["p_value"] < 0.05 for res in ks_results.values())
    if any_bias:
        LOG.info("Bias detected (p < 0.05). Computing inverse‑probability weights.")
        # Compute a weight per property and then average them.
        weight_arrays = []
        for name, full_arr, aligned_arr in [
            ("dipole", full_qm9_df["dipole"].to_numpy(), dip_aligned),
            ("polarizability", full_qm9_df["polarizability"].to_numpy(), pol_aligned),
            ("gap", full_qm9_df["gap"].to_numpy(), gap_aligned),
        ]:
            w = _compute_weights(full_arr, aligned_arr)
            weight_arrays.append(w)

        # Average the three weight vectors (arithmetic mean)
        weight_mask = np.mean(np.stack(weight_arrays, axis=0), axis=0).astype(np.float32)

        weight_path = paths.data("processed", "weight_mask.npy")
        np.save(weight_path, weight_mask)
        LOG.info("Saved weight mask to %s (shape %s)", weight_path, weight_mask.shape)
    else:
        LOG.info("No significant selection bias detected; no weight mask created.")

    LOG.info("Selection‑bias audit completed successfully")


if __name__ == "__main__":
    # The script is intended to be run via ``python code/data/bias_audit.py``.
    # Any exception will be logged and cause a non‑zero exit code, which
    # satisfies the “fast‑failure on error” requirement.
    try:
        main()
    except Exception as exc:
        LOG.error("Bias audit failed: %s", exc, exc_info=True)
        raise   # Re‑raise to propagate a non‑zero exit status.