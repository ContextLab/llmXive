"""
Analysis of twin prime normalized gaps.

Implements the Parametric Bootstrap Kolmogorov–Smirnov test (FR‑003) and
generates a QQ‑plot (FR‑004). Results are written to
`data/results/stats.json` and `data/figures/qq_plot.png`.
"""
import json
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt

from llmxive_toolkit import paths
from utils import setup_logging, exit_with_error

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def get_csv_path() -> Path:
    """
    Return the absolute path of the twin‑prime CSV dataset.
    """
    return paths.data("raw", "twin_primes.csv")


def load_twin_primes(csv_path: Path = None) -> pd.DataFrame:
    """
    Load and validate the twin‑prime gap dataset.

    Parameters
    ----------
    csv_path : Path, optional
        Path to the CSV file; if omitted the default location is used.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ``p``, ``p_next``, ``delta``,
        ``normalized_gap``.
    """
    if csv_path is None:
        csv_path = get_csv_path()

    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset not found at {csv_path}")

    df = pd.read_csv(csv_path)

    required = ["p", "p_next", "delta", "normalized_gap"]
    if list(df.columns) != required:
        raise ValueError(
            f"CSV columns mismatch. Expected {required}, got {list(df.columns)}"
        )

    if df["normalized_gap"].isna().any():
        raise ValueError("NaN values found in normalized_gap column")

    if not np.all(df["normalized_gap"] > 0):
        raise ValueError("Non‑positive values in normalized_gap column")

    return df


def load_gap_arrays(csv_path: Path = None) -> tuple[np.ndarray, np.ndarray]:
    """
    Convenience loader returning ``(p, normalized_gap)`` numpy arrays.

    Parameters
    ----------
    csv_path : Path, optional
        Path to the CSV file.

    Returns
    -------
    tuple (np.ndarray, np.ndarray)
        ``p`` values and corresponding ``normalized_gap`` values.
    """
    df = load_twin_primes(csv_path)
    return df["p"].to_numpy(dtype=np.int64), df["normalized_gap"].to_numpy(dtype=np.float64)


# ----------------------------------------------------------------------
# Core analysis
# ----------------------------------------------------------------------
def _bootstrap_ks(
    data: np.ndarray,
    dist: stats.rv_continuous,
    n_iter: int = 10_000,
    seed: int = 42,
) -> tuple[float, float]:
    """
    Perform a parametric bootstrap KS test.

    Parameters
    ----------
    data : np.ndarray
        Empirical sample.
    dist : scipy.stats.rv_continuous
        Theoretical distribution (already frozen with required parameters).
    n_iter : int
        Number of bootstrap repetitions.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    ks_stat : float
        Observed KS statistic.
    p_val : float
        Bootstrap‑based p‑value.
    """
    rng = np.random.default_rng(seed)

    # Observed KS statistic
    ks_stat, _ = stats.kstest(data, dist.cdf)

    # Generate bootstrap statistics
    boot_stats = np.empty(n_iter, dtype=np.float64)
    size = data.shape[0]

    for i in range(n_iter):
        sample = dist.rvs(size=size, random_state=rng)
        boot_stats[i], _ = stats.kstest(sample, dist.cdf)

    # p‑value = proportion of bootstrap stats >= observed
    p_val = np.mean(boot_stats >= ks_stat)
    return ks_stat, p_val


def _save_stats(stats_path: Path, ks_stat: float, p_val: float) -> None:
    """
    Write the KS results to ``stats.json`` with the required schema.
    """
    rejection = p_val < 0.05
    payload = {
        "ks_statistic": float(ks_stat),
        "p_value": float(p_val),
        "rejection_status": bool(rejection),
    }
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def _create_qq_plot(data: np.ndarray, dist: stats.rv_continuous, png_path: Path) -> None:
    """
    Generate a QQ‑plot of the empirical data versus the theoretical
    exponential distribution and save it as a PNG.
    """
    # Empirical quantiles
    sorted_data = np.sort(data)
    n = len(sorted_data)
    probs = (np.arange(1, n + 1) - 0.5) / n

    # Theoretical quantiles from the exponential distribution
    theoretical = dist.ppf(probs)

    plt.figure(figsize=(6, 6))
    plt.scatter(theoretical, sorted_data, s=10, alpha=0.6, label="Empirical")
    max_val = max(theoretical.max(), sorted_data.max())
    plt.plot([0, max_val], [0, max_val], "r--", label="y = x")
    plt.xlabel("Theoretical Quantiles (Exponential, λ=1)")
    plt.ylabel("Empirical Normalized Gaps")
    plt.title("QQ‑Plot: Empirical vs Exponential(λ=1)")
    plt.legend()
    plt.grid(True, linestyle=":", alpha=0.7)

    png_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(png_path, dpi=150)
    plt.close()


def main() -> int:
    """
    Entry point for the analysis pipeline.

    Executes the bootstrap KS test, writes ``stats.json`` and the QQ‑plot,
    and logs progress. Returns exit code 0 on success, non‑zero on failure.
    """
    logger: logging.Logger = setup_logging("analyze_gaps")
    start = time.time()

    try:
        # Load data
        _, norm_gap = load_gap_arrays()
        logger.info("Loaded %d normalized gap values.", norm_gap.size)

        # Theoretical distribution: Exponential with scale=1 (λ=1)
        exp_dist = stats.expon(scale=1)

        # Parametric bootstrap KS test
        ks_stat, p_val = _bootstrap_ks(
            data=norm_gap,
            dist=exp_dist,
            n_iter=10_000,
            seed=42,
        )
        logger.info("Bootstrap KS statistic = %.6f, p‑value = %.6f", ks_stat, p_val)

        # Save JSON results
        stats_path = paths.results("stats.json")
        _save_stats(stats_path, ks_stat, p_val)
        logger.info("Saved KS results to %s", stats_path)

        # Generate QQ‑plot
        qq_path = paths.figures("qq_plot.png")
        _create_qq_plot(norm_gap, exp_dist, qq_path)
        logger.info("Saved QQ‑plot to %s", qq_path)

        elapsed = time.time() - start
        logger.info("Analysis completed in %.2f seconds.", elapsed)
        return 0

    except Exception as exc:
        logger.error("Analysis failed: %s", exc)
        exit_with_error(str(exc), code=1)
        return 1  # Unreachable, but for type‑checkers


if __name__ == "__main__":
    import sys

    sys.exit(main())
