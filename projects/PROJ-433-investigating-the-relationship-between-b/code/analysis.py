import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
from scipy.stats import spearmanr

# Public API surface (as declared in the project specification)
__all__ = [
    "load_metrics_and_behavioral_data",
    "compute_spearman",
    "apply_bonferroni",
    "compute_cohens_r",
    "handle_extreme_p_values",
    "save_aggregated_statistics",
    "run_permutation_test",
    "calculate_permutation_p_value",
    "main",
]

logger = logging.getLogger(__name__)


def load_metrics_and_behavioral_data(
    metrics_dir: Path = Path("data/results"),
    behavior_path: Path = Path("data/processed/behavior.tsv"),
) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    Load metric values and behavioral scores.

    Returns
    -------
    metrics : dict
        Mapping from subject_id to metric value (e.g., reconfigurability).
    behavior : dict
        Mapping from subject_id to DSST score (or other behavioral measure).
    """
    # The concrete implementation was provided in earlier tasks.
    # Here we import the original implementation to keep the public API stable.
    # If the original function does not exist, this will raise an ImportError,
    # which is appropriate because the pipeline cannot continue without real data.
    from .analysis import load_metrics_and_behavioral_data as _original_load

    return _original_load(metrics_dir=metrics_dir, behavior_path=behavior_path)


def compute_spearman(
    metric_vals: List[float], behavior_vals: List[float]
) -> Tuple[float, float]:
    """
    Compute Spearman rank correlation between a metric and a behavioral score.

    Parameters
    ----------
    metric_vals : list of float
        Metric values for each subject.
    behavior_vals : list of float
        Corresponding behavioral scores.

    Returns
    -------
    rho : float
        Spearman correlation coefficient.
    p_val : float
        Two‑tailed p‑value.
    """
    rho, p_val = spearmanr(metric_vals, behavior_vals, nan_policy="omit")
    return float(rho), float(p_val)


def apply_bonferroni(p_vals: List[float]) -> List[float]:
    """
    Apply Bonferroni correction to a list of p‑values.

    Parameters
    ----------
    p_vals : list of float
        Unadjusted p‑values.

    Returns
    -------
    adjusted : list of float
        Bonferroni‑adjusted p‑values, capped at 1.0.
    """
    n = len(p_vals)
    return [min(p * n, 1.0) for p in p_vals]


def compute_cohens_r(rho: float, n: int) -> float:
    """
    Compute Cohen's *r* effect size from Spearman's rho.

    Parameters
    ----------
    rho : float
        Spearman correlation coefficient.
    n : int
        Number of valid observations.

    Returns
    -------
    r : float
        Cohen's r.
    """
    if n <= 2:
        raise ValueError("At least 3 observations are required for effect size.")
    return rho * np.sqrt((n - 2) / (1 - rho ** 2))


def handle_extreme_p_values(p_vals: List[float], floor: float = 1e-12) -> List[float]:
    """
    Clamp extremely small p‑values to a floor to avoid division‑by‑zero downstream.

    Parameters
    ----------
    p_vals : list of float
        Raw p‑values.
    floor : float, default 1e-12
        Minimum allowed p‑value.

    Returns
    -------
    clamped : list of float
        p‑values with a lower bound applied.
    """
    return [max(p, floor) for p in p_vals]


def save_aggregated_statistics(
    results: List[Dict[str, Any]],
    output_path: Path = Path("data/analysis_results.tsv"),
) -> None:
    """
    Write the aggregated statistical summary to a TSV file.

    The file contains the following columns:
    ``metric_pair``   – Identifier of the metric/behavior pair (e.g. ``reconfigurability_vs_DSAT``)
    ``spearman_rho``  – Spearman correlation coefficient
    ``p_val``         – Unadjusted p‑value
    ``p_adj``         – Bonferroni‑adjusted p‑value
    ``cohens_r``      – Cohen's r effect size

    Parameters
    ----------
    results : list of dict
        Each dict must contain the keys ``metric_pair``, ``spearman_rho``,
        ``p_val``, ``p_adj`` and ``cohens_r``.
    output_path : pathlib.Path, optional
        Destination TSV file. Parent directories are created if missing.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    header = ["metric_pair", "spearman_rho", "p_val", "p_adj", "cohens_r"]
    with output_path.open("w", encoding="utf-8") as f:
        f.write("\t".join(header) + "\n")
        for row in results:
            line = "\t".join(
                [
                    str(row.get(col, "")) for col in header
                ]
            )
            f.write(line + "\n")
    logger.info(f"Aggregated analysis results written to {output_path}")


def run_permutation_test(
    metric_vals: List[float],
    behavior_vals: List[float],
    n_permutations: int = 1000,
    rng_seed: int = 42,
) -> np.ndarray:
    """
    Perform a permutation test by shuffling the behavioral scores.

    Returns an array of permuted Spearman rho values.
    """
    rng = np.random.default_rng(rng_seed)
    permuted_rhos = np.empty(n_permutations, dtype=float)

    for i in range(n_permutations):
        shuffled = rng.permutation(behavior_vals)
        rho, _ = spearmanr(metric_vals, shuffled, nan_policy="omit")
        permuted_rhos[i] = rho

    return permuted_rhos


def calculate_permutation_p_value(
    observed_rho: float, permuted_rhos: np.ndarray
) -> float:
    """
    Compute a two‑tailed permutation p‑value.
    """
    more_extreme = np.sum(np.abs(permuted_rhos) >= np.abs(observed_rho))
    return (more_extreme + 1) / (len(permuted_rhos) + 1)


def main() -> None:
    """
    End‑to‑end driver for the statistical analysis stage.

    1. Load metric and behavioral data.
    2. For each metric‑behavior pair compute Spearman rho and p‑value.
    3. Apply Bonferroni correction.
    4. Compute Cohen's r effect size.
    5. Clamp extreme p‑values.
    6. Write the aggregated TSV file.
    """
    # Load data
    try:
        metrics_dict, behavior_dict = load_metrics_and_behavioral_data()
    except Exception as exc:
        logger.error(f"Failed to load data for analysis: {exc}")
        raise

    # Align subjects present in both dictionaries
    common_subjects = set(metrics_dict) & set(behavior_dict)
    if not common_subjects:
        raise RuntimeError("No overlapping subjects between metrics and behavior data.")

    metric_vals = [metrics_dict[s] for s in common_subjects]
    behavior_vals = [behavior_dict[s] for s in common_subjects]
    n = len(common_subjects)

    # Compute Spearman correlation
    rho, p_val = compute_spearman(metric_vals, behavior_vals)

    # Bonferroni adjustment (only one test here, but keep generic)
    p_adj = apply_bonferroni([p_val])[0]

    # Effect size
    cohens_r = compute_cohens_r(rho, n)

    # Clamp extreme p‑values (both raw and adjusted)
    p_val, p_adj = handle_extreme_p_values([p_val, p_adj])

    # Assemble result
    results = [
        {
            "metric_pair": "reconfigurability_vs_DSAT",
            "spearman_rho": rho,
            "p_val": p_val,
            "p_adj": p_adj,
            "cohens_r": cohens_r,
        }
    ]

    # Write TSV
    save_aggregated_statistics(results)

    logger.info("Statistical analysis completed successfully.")


if __name__ == "__main__":
    # When the module is executed directly, run the analysis pipeline.
    logging.basicConfig(level=logging.INFO)
    main()