"""Correlation fidelity metrics: Pearson/Spearman diffs, Fisher-z deviations,
permutation-based correlation-difference tests (FR-004, FR-005; Principle VI)."""
from __future__ import annotations

import logging
from itertools import combinations
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy import stats

log = logging.getLogger(__name__)

FISHER_Z_CLIP = 0.999


def correlation_matrices(
    df: pd.DataFrame, cols: Sequence[str]
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Pearson and Spearman correlation matrices over the given columns."""
    sub = df[list(cols)].apply(pd.to_numeric, errors="coerce")
    pearson = sub.corr(method="pearson")
    spearman = sub.corr(method="spearman")
    return pearson, spearman


def fisher_z(r: float) -> float:
    """Fisher z-transform of a correlation, clipped to [-0.999, 0.999] (Principle VI)."""
    r = float(r)
    if not np.isfinite(r):
        return float("nan")
    r = np.clip(r, -FISHER_Z_CLIP, FISHER_Z_CLIP)
    return float(np.arctanh(r))


def fisher_z_deviation(r_real: float, r_synth: float) -> float:
    """Absolute Fisher-z deviation |atanh(r_real) - atanh(r_synth)| between correlations."""
    zr = fisher_z(r_real)
    zs = fisher_z(r_synth)
    if not np.isfinite(zr) or not np.isfinite(zs):
        return float("nan")
    return float(abs(zr - zs))


def permutation_correlation_test(
    real_df: pd.DataFrame,
    synth_df: pd.DataFrame,
    col_a: str,
    col_b: str,
    n_permutations: int = 1000,
    seed: int = 42,
) -> Dict:
    """Permutation test for a difference in Pearson correlation between real and synthetic.

    Statistic: |r_real(a,b) - r_synth(a,b)|. Under the null (both samples drawn
    from the same joint distribution), group labels (real vs synthetic) are
    exchangeable, so we permute the labels of the pooled sample and recompute
    the statistic. Fixed seed for reproducibility; >= 1000 permutations.
    """
    if n_permutations < 1000:
        raise ValueError("FR-005 requires at least 1000 permutations")
    ra = pd.to_numeric(real_df[col_a], errors="coerce").to_numpy(dtype=float)
    rb = pd.to_numeric(real_df[col_b], errors="coerce").to_numpy(dtype=float)
    sa = pd.to_numeric(synth_df[col_a], errors="coerce").to_numpy(dtype=float)
    sb = pd.to_numeric(synth_df[col_b], errors="coerce").to_numpy(dtype=float)
    mask_r = np.isfinite(ra) & np.isfinite(rb)
    mask_s = np.isfinite(sa) & np.isfinite(sb)
    ra, rb = ra[mask_r], rb[mask_r]
    sa, sb = sa[mask_s], sb[mask_s]
    n_r, n_s = ra.size, sa.size
    if n_r < 3 or n_s < 3:
        return {
            "statistic": float("nan"),
            "pvalue": float("nan"),
            "n_permutations": n_permutations,
            "seed": seed,
        }

    def _diff(x: np.ndarray, y: np.ndarray, nr: int) -> float:
        r1 = np.corrcoef(x[:nr], y[:nr])[0, 1]
        r2 = np.corrcoef(x[nr:], y[nr:])[0, 1]
        if not (np.isfinite(r1) and np.isfinite(r2)):
            return float("nan")
        return abs(r1 - r2)

    xa = np.concatenate([ra, sa])
    xb = np.concatenate([rb, sb])
    observed = _diff(xa, xb, n_r)
    rng = np.random.default_rng(seed)
    count = 0
    valid = 0
    for _ in range(n_permutations):
        perm = rng.permutation(xa.size)
        d = _diff(xa[perm], xb[perm], n_r)
        if np.isfinite(d):
            valid += 1
            if d >= observed:
                count += 1
    pvalue = (count + 1) / (valid + 1) if valid > 0 else float("nan")
    return {
        "statistic": float(observed),
        "pvalue": float(pvalue),
        "n_permutations": n_permutations,
        "seed": seed,
    }


def _safe_corr(x: np.ndarray, y: np.ndarray, method: str) -> float:
    if x.size < 3:
        return float("nan")
    if method == "pearson":
        r = np.corrcoef(x, y)[0, 1]
    else:
        r = stats.spearmanr(x, y).statistic
    return float(r) if np.isfinite(r) else float("nan")


def compute_correlation_metrics(
    real_df: pd.DataFrame,
    synth_df: pd.DataFrame,
    cols: Optional[Sequence[str]] = None,
    n_permutations: int = 1000,
    seed: int = 42,
    max_pairs: Optional[int] = None,
) -> List[Dict]:
    """Per-column-pair correlation fidelity rows.

    For every pair of columns emits rows with metric_type PearsonDiff,
    SpearmanDiff, FisherZ (Principle VI) and PermutationCorr. Each row carries
    the real and synthetic coefficients, the absolute difference, the Fisher-z
    deviation, and (for PermutationCorr) the permutation-test statistic/p-value.
    """
    if cols is None:
        from src.metrics.marginal import detect_column_types

        cont, _ = detect_column_types(real_df)
        cols = [c for c in cont if c in synth_df.columns]
    cols = [c for c in cols if c in real_df.columns and c in synth_df.columns]
    pearson_r, spearman_r = correlation_matrices(real_df, cols)
    pearson_s, spearman_s = correlation_matrices(synth_df, cols)
    pairs = list(combinations(cols, 2))
    if max_pairs is not None:
        pairs = pairs[:max_pairs]
    rows: List[Dict] = []
    for col_a, col_b in pairs:
        pr_r = pearson_r.loc[col_a, col_b]
        pr_s = pearson_s.loc[col_a, col_b]
        sp_r = spearman_r.loc[col_a, col_b]
        sp_s = spearman_s.loc[col_a, col_b]
        base = {
            "column_a": col_a,
            "column_b": col_b,
            "real_pearson": float(pr_r) if np.isfinite(pr_r) else None,
            "synth_pearson": float(pr_s) if np.isfinite(pr_s) else None,
            "real_spearman": float(sp_r) if np.isfinite(sp_r) else None,
            "synth_spearman": float(sp_s) if np.isfinite(sp_s) else None,
            "pearson_diff": abs(pr_r - pr_s) if np.isfinite(pr_r) and np.isfinite(pr_s) else None,
            "spearman_diff": abs(sp_r - sp_s) if np.isfinite(sp_r) and np.isfinite(sp_s) else None,
            "fisher_z_deviation": fisher_z_deviation(pr_r, pr_s),
        }
        rows.append({**base, "metric_type": "PearsonDiff", "statistic": base["pearson_diff"]})
        rows.append({**base, "metric_type": "SpearmanDiff", "statistic": base["spearman_diff"]})
        rows.append(
            {
                **base,
                "metric_type": "FisherZ",
                "statistic": base["fisher_z_deviation"],
            }
        )
        perm = permutation_correlation_test(
            real_df, synth_df, col_a, col_b, n_permutations=n_permutations, seed=seed
        )
        rows.append(
            {
                **base,
                "metric_type": "PermutationCorr",
                "statistic": perm["statistic"],
                "pvalue": perm["pvalue"],
                "n_permutations": perm["n_permutations"],
                "seed": perm["seed"],
            }
        )
    return rows