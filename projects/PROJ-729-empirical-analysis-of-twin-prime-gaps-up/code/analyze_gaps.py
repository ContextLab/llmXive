"""T020 [US2]: Load the twin-prime gap dataset for statistical analysis.

This module implements the data-loading stage of User Story 2. It reads
data/raw/twin_primes.csv (produced by T012/T014), validates it against
the project's expectations (columns p, p_next, delta, normalized_gap;
finite, positive normalized gaps), and exposes the loaded arrays for
downstream statistical tests (Parametric Bootstrap KS in T021, QQ-plot
in T022).

The script is runnable as a CLI: it loads the REAL dataset from disk
(never synthetic data), logs a summary of what was loaded, and exits
non-zero if the dataset is missing or malformed so downstream tasks
fail loudly rather than silently.

Note on the data: the normalized_gap column is self-normalized
(delta / log(p) computed from the same twin-prime list), which is why
the downstream goodness-of-fit test (T021) must use a Parametric
Bootstrap rather than standard KS tables.
"""
import sys
import logging
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

from llmxive_toolkit import paths

REQUIRED_COLUMNS = ["p", "p_next", "delta", "normalized_gap"]

logger = logging.getLogger(__name__)


def get_csv_path() -> Path:
    """Return the absolute path of the twin-prime CSV dataset."""
    return paths.data("raw", "twin_primes.csv")


def load_twin_primes(csv_path: Path = None) -> pd.DataFrame:
    """Load and validate the twin-prime gap dataset.

    Args:
        csv_path: Optional explicit path; defaults to
            data/raw/twin_primes.csv inside the project.

    Returns:
        A pandas DataFrame with columns p, p_next, delta,
        normalized_gap.

    Raises:
        FileNotFoundError: if the CSV does not exist (T012 must run first).
        ValueError: if columns are missing or normalized_gap contains
            NaN / non-finite / non-positive values.
    """
    path = Path(csv_path) if csv_path is not None else get_csv_path()
    if not path.exists():
        raise FileNotFoundError(
            f"Twin prime dataset not found at {path}. "
            "Run code/generate_primes.py (T012) before the analysis."
        )

    logger.info("Loading twin prime dataset from %s", path)
    df = pd.read_csv(path)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"Dataset {path} is missing required columns: {missing}. "
            f"Found columns: {list(df.columns)}"
        )
    if len(df) == 0:
        raise ValueError(f"Dataset {path} contains no data rows.")

    gaps = df["normalized_gap"].to_numpy(dtype=np.float64)
    if not np.all(np.isfinite(gaps)):
        raise ValueError("normalized_gap contains NaN or infinite values.")
    if not np.all(gaps > 0):
        raise ValueError("normalized_gap contains non-positive values.")

    logger.info(
        "Loaded %d twin-prime rows; normalized_gap in [%.6f, %.6f], "
        "mean %.6f",
        len(df), float(gaps.min()), float(gaps.max()), float(gaps.mean()),
    )
    return df


def load_gap_arrays(csv_path: Path = None) -> Tuple[np.ndarray, np.ndarray]:
    """Convenience loader returning (p, normalized_gap) numpy arrays."""
    df = load_twin_primes(csv_path)
    return (
        df["p"].to_numpy(dtype=np.int64),
        df["normalized_gap"].to_numpy(dtype=np.float64),
    )


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    try:
        df = load_twin_primes()
    except (FileNotFoundError, ValueError) as exc:
        logger.error("Failed to load twin prime dataset: %s", exc)
        return 1

    gaps = df["normalized_gap"].to_numpy(dtype=np.float64)
    summary = {
        "rows_loaded": int(len(df)),
        "columns": REQUIRED_COLUMNS,
        "normalized_gap_min": float(gaps.min()),
        "normalized_gap_max": float(gaps.max()),
        "normalized_gap_mean": float(gaps.mean()),
        "normalized_gap_std": float(gaps.std(ddof=1)),
        "all_finite_positive": True,
    }
    logger.info("Load summary: %s", summary)
    print(f"Loaded {summary['rows_loaded']} rows from {get_csv_path()}")
    print(
        "normalized_gap: mean={mean:.6f} std={std:.6f} "
        "min={mn:.6f} max={mx:.6f}".format(
            mean=summary["normalized_gap_mean"],
            std=summary["normalized_gap_std"],
            mn=summary["normalized_gap_min"],
            mx=summary["normalized_gap_max"],
        )
    )
    logger.info(
        "T020 complete: dataset loaded and validated; ready for "
        "Parametric Bootstrap KS testing (T021)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())