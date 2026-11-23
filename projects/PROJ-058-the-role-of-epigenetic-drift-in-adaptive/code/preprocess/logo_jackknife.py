"""
Leave-One-Generation-Out (LOGO) jackknife logic (Task T016, US1).

This module implements the LOGO jackknife variance derivation shared by
the RNA-seq (``code/preprocess/rna_seq.py``) and methylation
(``code/preprocess/methyl.py``) preprocessing streams. It exists as an
isolated module so that both omics layers can derive per-gene variance
from *independent* sample subsets, breaking the circular validation
where the variance of Layer A and Layer B are computed from the exact
same N samples (Constitution Principle VI, plan.md).

Two complementary mechanisms are provided:

1. **LOGO jackknife** (``logo_jackknife_variance``): for each unique
   generation, the variance statistic is recomputed on the subset that
   *excludes* that generation. The jackknife pseudovalues then yield a
   bias-reduced point estimate plus a standard error / confidence
   interval, acknowledging N<10 instability (plan.md, validation step).
2. **Disjoint generation split** (``disjoint_generation_split``): the
   sample generations are partitioned into two disjoint subsets (odd /
   even generation index) so that Layer A (e.g. methylation) and Layer B
   (e.g. RNA-seq) variances can be derived from non-overlapping samples,
   as mandated by plan.md ("variance of Layer A is derived from disjoint
   sample subsets (e.g., odd generations) compared to Layer B (even
   generations)").

This module is a pure computation library: it contains no data loading
and no synthetic fallbacks.
"""

import logging
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

__all__ = [
    "logo_folds",
    "disjoint_generation_split",
    "compute_cv",
    "compute_variance",
    "logo_jackknife_variance",
    "logo_jackknife_from_long",
    "cross_layer_logo_split",
]

# Default variance statistic: coefficient of variation, as specified in
# the research methodology ("per-gene epigenetic variance across
# generations using coefficient of variation (CV)").
def compute_cv(values: Sequence[float]) -> float:
    """Coefficient of variation (population std / mean).

    Returns 0.0 when the mean is zero (guards division by zero for
    zero-expression genes, see spec edge cases).
    """
    arr = np.asarray(values, dtype=float)
    arr = arr[~np.isnan(arr)]
    if arr.size == 0:
        return 0.0
    mean = float(np.mean(arr))
    if mean == 0.0:
        return 0.0
    return float(np.std(arr) / abs(mean))

def compute_variance(values: Sequence[float]) -> float:
    """Plain population variance, ignoring NaNs."""
    arr = np.asarray(values, dtype=float)
    arr = arr[~np.isnan(arr)]
    if arr.size == 0:
        return 0.0
    return float(np.var(arr))

DEFAULT_VARIANCE_FN: Callable[[Sequence[float]], float] = compute_cv

def logo_folds(generation_labels: Sequence) -> List[Tuple[np.ndarray, np.ndarray]]:
    """Build Leave-One-Generation-Out folds.

    Args:
        generation_labels: per-sample generation identifiers.

    Returns:
        List of ``(train_idx, held_out_idx)`` index arrays. ``train_idx``
        contains all samples NOT belonging to the held-out generation;
        ``held_out_idx`` contains the samples of that generation. Every
        sample appears in exactly one held-out set, and no sample appears
        in both the train and held-out set of the same fold (the subsets
        are disjoint by construction).
    """
    labels = np.asarray(list(generation_labels))
    unique_generations = sorted(set(labels.tolist()))
    folds: List[Tuple[np.ndarray, np.ndarray]] = []
    for gen in unique_generations:
        held_out_idx = np.where(labels == gen)[0]
        train_idx = np.where(labels != gen)[0]
        folds.append((train_idx, held_out_idx))
    return folds

def disjoint_generation_split(
    generation_labels: Sequence,
) -> Tuple[List[int], List[int]]:
    """Partition sample indices into two disjoint generation subsets.

    Layer A receives samples from odd-ranked unique generations, Layer B
    from even-ranked unique generations (ranked by sorted generation
    order). If only one generation exists, Layer B is empty and the
    caller must treat the split as unavailable.

    Returns:
        ``(layer_a_indices, layer_b_indices)`` — disjoint lists of
        positional sample indices.
    """
    labels = np.asarray(list(generation_labels))
    unique_generations = sorted(set(labels.tolist()))
    layer_a: List[int] = []
    layer_b: List[int] = []
    for rank, gen in enumerate(unique_generations):
        idx = np.where(labels == gen)[0].tolist()
        if rank % 2 == 0:
            layer_a.extend(idx)
        else:
            layer_b.extend(idx)
    return layer_a, layer_b

def logo_jackknife_variance(
    values: Sequence[float],
    generation_labels: Sequence,
    variance_fn: Callable[[Sequence[float]], float] = DEFAULT_VARIANCE_FN,
    confidence: float = 0.95,
) -> Dict[str, Optional[float]]:
    """LOGO jackknife variance estimate for a single gene / feature.

    For each unique generation g, the variance statistic is recomputed
    on the samples excluding g (``theta_hat_g``). The jackknife point
    estimate is the mean of the ``theta_hat_g``; pseudovalues
    ``n * theta_all - (n - 1) * theta_hat_g`` provide the standard
    error and a normal-approximation confidence interval.

    Args:
        values: per-sample measurements for one feature.
        generation_labels: per-sample generation identifiers.
        variance_fn: statistic to jackknife (default: CV).
        confidence: CI coverage (default 0.95).

    Returns:
        Dict with keys ``estimate``, ``std_error``, ``ci_lower``,
        ``ci_upper``, ``n_folds``, ``n_samples``.
    """
    from scipy import stats as _stats

    arr = np.asarray(values, dtype=float)
    labels = np.asarray(list(generation_labels))
    if arr.shape != labels.shape:
        raise ValueError(
          "values and generation_labels must have the same length "
          f"(got {arr.shape[0]} and {labels.shape[0]})"
        )

    folds = logo_folds(labels)
    n_folds = len(folds)
    result: Dict[str, Optional[float]] = {
        "estimate": None,
        "std_error": None,
        "ci_lower": None,
        "ci_upper": None,
        "n_folds": n_folds,
        "n_samples": int(arr.size),
    }
    if n_folds == 0:
        return result

    theta_all = float(variance_fn(arr))

    if n_folds == 1:
        # Cannot leave one out of a single generation; report the raw
        # statistic with no uncertainty quantification.
        result["estimate"] = theta_all
        return result

    theta_folds = np.array(
        [float(variance_fn(arr[train_idx])) for train_idx, _ in folds],
        dtype=float,
    )
    n = n_folds
    pseudovalues = n * theta_all - (n - 1) * theta_folds
    estimate = float(np.mean(pseudovalues))
    std_error = float(np.std(pseudovalues, ddof=1) / np.sqrt(n)) if n > 1 else 0.0
    z = float(_stats.norm.ppf(0.5 + confidence / 2.0))
    result["estimate"] = estimate
    result["std_error"] = std_error
    result["ci_lower"] = estimate - z * std_error
    result["ci_upper"] = estimate + z * std_error
    return result

def logo_jackknife_from_long(
    df: pd.DataFrame,
    feature_col: str,
    generation_col: str = "generation",
    sample_col: Optional[str] = None,
    value_col: str = "value",
    variance_fn: Callable[[Sequence[float]], float] = DEFAULT_VARIANCE_FN,
) -> pd.DataFrame:
    """Apply LOGO jackknife variance to every feature of a long table.

    Args:
        df: long-format dataframe with one row per (feature, sample).
        feature_col: column identifying genes / CpG groups.
        generation_col: column with the generation of each sample.
        sample_col: optional sample id column (used only for logging).
        value_col: column with the measured value.
        variance_fn: statistic to jackknife.

    Returns:
        Wide dataframe, one row per feature, with columns
        ``feature_col``, ``variance_estimate``, ``variance_std_error``,
        ``variance_ci_lower``, ``variance_ci_upper``, ``n_folds``,
        ``n_samples``.
    """
    required = {feature_col, generation_col, value_col}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    records: List[Dict[str, Optional[float]]] = []
    for feature, group in df.groupby(feature_col, sort=True):
        values = group[value_col].to_numpy(dtype=float)
        labels = group[generation_col].to_numpy()
        res = logo_jackknife_variance(values, labels, variance_fn=variance_fn)
        records.append(
            {
                feature_col: feature,
                "variance_estimate": res["estimate"],
                "variance_std_error": res["std_error"],
                "variance_ci_lower": res["ci_lower"],
                "variance_ci_upper": res["ci_upper"],
                "n_folds": res["n_folds"],
                "n_samples": res["n_samples"],
            }
        )
    out = pd.DataFrame.from_records(records)
    logger.info(
        "LOGO jackknife completed for %d features over %d rows",
        len(out),
        len(df),
    )
    return out

def cross_layer_logo_split(
    df: pd.DataFrame, generation_col: str = "generation"
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Split a sample-level dataframe into two disjoint generation subsets.

    Used to guarantee that the methylation stream (Layer A) and the
    RNA-seq stream (Layer B) derive their variances from independent
    sample subsets (odd vs. even ranked generations).

    Args:
        df: dataframe with one row per sample (or per feature-sample).
        generation_col: column containing the generation label.

    Returns:
        ``(layer_a, layer_b)`` dataframes with disjoint generation sets.
    """
    if generation_col not in df.columns:
        raise ValueError(
            f"Generation column '{generation_col}' not found in dataframe"
        )
    idx_a, idx_b = disjoint_generation_split(df[generation_col])
    layer_a = df.iloc[idx_a].copy()
    layer_b = df.iloc[idx_b].copy()
    if not layer_b.empty:
        shared = set(layer_a[generation_col]) & set(layer_b[generation_col])
        if shared:
            # Cannot happen by construction; fail loudly if it ever does.
            raise AssertionError(
                f"LOGO split leaked generations into both layers: {shared}"
            )
    logger.info(
        "Cross-layer LOGO split: layer A=%d rows, layer B=%d rows",
        len(layer_a),
        len(layer_b),
    )
    return layer_a, layer_b
