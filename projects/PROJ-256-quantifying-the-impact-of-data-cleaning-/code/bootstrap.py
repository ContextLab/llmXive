import json
import logging
import os
import random
from pathlib import Path
from typing import Callable, List, Any, Dict

import numpy as np
import pandas as pd

from config import get_config

logger = logging.getLogger(__name__)

def _default_statistic(data: pd.DataFrame) -> float:
    """Simple statistic – mean of the first numeric column."""
    numeric = data.select_dtypes(include=[np.number])
    if numeric.empty:
        return 0.0
    return float(numeric.iloc[:, 0].mean())

def run_bootstrap(
    data: pd.DataFrame,
    statistic_func: Callable[[pd.DataFrame], float] = _default_statistic,
    n_resamples: int = None,
    random_state: int = None,
) -> List[float]:
    """
    Perform a non‑parametric bootstrap.

    Parameters
    ----------
    data : pd.DataFrame
        Original data.
    statistic_func : callable, optional
        Function that computes the statistic of interest from a DataFrame.
    n_resamples : int, optional
        Number of bootstrap resamples. If ``None``, the value from
        ``config.BOOTSTRAP_ITERATIONS`` (default 1000) is used.
    random_state : int, optional
        Seed for reproducibility.

    Returns
    -------
    List[float]
        List of statistic values computed on each resampled dataset.
    """
    cfg = get_config()
    if n_resamples is None:
        n_resamples = getattr(cfg, "BOOTSTRAP_ITERATIONS", 1000)

    if n_resamples < 1000:
        logger.warning(
            f"Bootstrap iterations requested ({n_resamples}) are less than the "
            f"minimum required (1000). Using 1000."
        )
        n_resamples = 1000

    rng = np.random.default_rng(random_state)

    stats: List[float] = []
    n = len(data)
    for i in range(n_resamples):
        # Sample with replacement
        indices = rng.integers(0, n, size=n)
        sample = data.iloc[indices]
        stats.append(statistic_func(sample))

    return stats

def main():
    """
    Simple demonstration that reads a CSV from ``data/raw`` (if any),
    runs the bootstrap, and writes the results to
    ``data/processed/bootstrap_results.json``.
    """
    raw_dir = Path("data/raw")
    csv_files = list(raw_dir.glob("*.csv"))
    if not csv_files:
        logger.error("No raw CSV files found for bootstrap demonstration.")
        return

    df = pd.read_csv(csv_files[0])
    results = run_bootstrap(df)

    out_path = Path("data/processed/bootstrap_results.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as fp:
        json.dump({"bootstrap_results": results}, fp, indent=2)

    logger.info(f"Bootstrap results written to {out_path}")

if __name__ == "__main__":
    main()