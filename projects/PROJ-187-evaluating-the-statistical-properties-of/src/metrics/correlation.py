from __future__ import annotations

import logging
from itertools import combinations
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

def correlation_matrices(
    df: pd.DataFrame, cols: Sequence[str]
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Pearson and Spearman correlation matrices."""
    pearson = df[cols].corr(method="pearson")
    spearman = df[cols].corr(method="spearman")
    return pearson, spearman

def _safe_corr(x: np.ndarray, y: np.ndarray, method: str) -> float:
    if method == "pearson":
        return np.corrcoef(x, y)[0, 1]
    elif method == "spearman":
        return pd.Series(x).corr(pd.Series(y), method="spearman")
    else:
        raise ValueError("Unsupported method")

def fisher_z(r: float) -> float:
    """Fisher z‑transform of a correlation, clipped to [-0.999, 0.999]."""
    r = max(min(r, 0.999), -0.999)
    return np.arctanh(r)

def fisher_z_deviation(r_real: float, r_synth: float) -> float:
    """Absolute Fisher‑z deviation."""
    return abs(fisher_z(r_real) - fisher_z(r_synth))

def permutation_correlation_test(
    real_df: pd.DataFrame,
    synth_df: pd.DataFrame,
    col_a: str,
    col_b: str,
    n_permutations: int = 1000,
    seed: int = 42,
) -> Dict:
    """Permutation test for difference in Pearson correlation."""
    rng = np.random.default_rng(seed)
    real_corr = _safe_corr(real_df[col_a].values, real_df[col_b].values, "pearson")
    synth_corr = _safe_corr(synth_df[col_a].values, synth_df[col_b].values, "pearson")
    diff_obs = abs(real_corr - synth_corr)

    combined = pd.concat([real_df[[col_a, col_b]], synth_df[[col_a, col_b]]], ignore_index=True)
    diffs = []
    for _ in range(n_permutations):
        perm = combined.sample(frac=1.0, random_state=rng.integers(0, 1_000_000), replace=False)
        perm_real = perm.iloc[: len(real_df)]
        perm_synth = perm.iloc[len(real_df) :]
        perm_real_corr = _safe_corr(perm_real[col_a].values, perm_real[col_b].values, "pearson")
        perm_synth_corr = _safe_corr(perm_synth[col_a].values, perm_synth[col_b].values, "pearson")
        diffs.append(abs(perm_real_corr - perm_synth_corr))
    p_val = (np.sum(np.array(diffs) >= diff_obs) + 1) / (n_permutations + 1)
    return {
        "col_pair": (col_a, col_b),
        "real_corr": real_corr,
        "synth_corr": synth_corr,
        "abs_diff": diff_obs,
        "p_value": p_val,
    }

def compute_correlation_metrics(
    real_df: pd.DataFrame,
    synth_df: pd.DataFrame,
    cols: Optional[Sequence[str]] = None,
    n_permutations: int = 1000,
    seed: int = 42,
    max_pairs: Optional[int] = None,
) -> List[Dict]:
    """Per‑column‑pair correlation fidelity rows."""
    if cols is None:
        cols = real_df.select_dtypes(include=[np.number]).columns.tolist()
    pairs = list(combinations(cols, 2))
    if max_pairs is not None:
        pairs = pairs[:max_pairs]
    results = []
    for a, b in pairs:
        real_corr = _safe_corr(real_df[a].values, real_df[b].values, "pearson")
        synth_corr = _safe_corr(synth_df[a].values, synth_df[b].values, "pearson")
        spearman_real = _safe_corr(real_df[a].values, real_df[b].values, "spearman")
        spearman_synth = _safe_corr(synth_df[a].values, synth_df[b].values, "spearman")
        fisher_dev = fisher_z_deviation(real_corr, synth_corr)
        perm_test = permutation_correlation_test(
            real_df, synth_df, a, b, n_permutations=n_permutations, seed=seed
        )
        results.append(
            {
                "col_pair": (a, b),
                "pearson_real": real_corr,
                "pearson_synth": synth_corr,
                "pearson_diff": abs(real_corr - synth_corr),
                "spearman_real": spearman_real,
                "spearman_synth": spearman_synth,
                "spearman_diff": abs(spearman_real - spearman_synth),
                "fisher_z_deviation": fisher_dev,
                "permutation_pvalue": perm_test["p_value"],
            }
        )
    return results