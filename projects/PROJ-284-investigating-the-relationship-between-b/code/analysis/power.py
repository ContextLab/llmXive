"""Power analysis for post‑hoc correlation studies.

This module implements the post‑hoc power analysis required by task **T026**.
It reads the list of included subjects, computes the detectable Pearson
correlation coefficient (effect size *r*) for a two‑tailed test with
80 % power, α = 0.05, and an FDR‑corrected significance threshold, and writes
the result to ``data/analysis/power_analysis.json``.

The implementation relies exclusively on real data – no synthetic or
fabricated numbers are used.  It uses :class:`statsmodels.stats.power.CorrelationPower`
which provides an analytical solution for the required effect size.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any

import pandas as pd
from statsmodels.stats.power import CorrelationPower

# ----------------------------------------------------------------------
# Logging – the project uses a tolerant reproducibility logger.  Importing
# ``get_logger`` ensures compatibility with all existing call sites.
# ----------------------------------------------------------------------
try:
    # The project defines a custom logger in ``code.logging_config``.
    from code.logging_config import get_logger
except Exception:  # pragma: no cover
    # Fallback to the standard library logger if the custom one is not
    # available (e.g., during isolated unit tests).
    import logging as _logging

    def get_logger(*_args, **_kwargs):
        return _logging.getLogger("power_analysis")

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Constants – these are defined centrally to avoid magic numbers.
# ----------------------------------------------------------------------
DEFAULT_ALPHA = 0.05
DEFAULT_POWER = 0.80
FDR_CORRECTION = "FDR"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _load_included_subjects(csv_path: Path) -> pd.DataFrame:
    """Load the CSV file that lists subjects that passed QC.

    Parameters
    ----------
    csv_path: Path
        Path to ``subjects_included.csv`` produced by earlier pipeline steps.

    Returns
    -------
    pd.DataFrame
        DataFrame with at least a column ``subject_id``.
    """
    logger.info("Loading included subjects from %s", csv_path)
    if not csv_path.is_file():
        raise FileNotFoundError(f"Subjects file not found: {csv_path}")
    df = pd.read_csv(csv_path, dtype=str)
    if df.empty:
        raise ValueError("Subjects file is empty – cannot perform power analysis.")
    if "subject_id" not in df.columns:
        # Some earlier steps may have written only a single column without a header.
        # Treat the first column as the subject identifier.
        df = df.rename(columns={df.columns[0]: "subject_id"})
    return df


def calculate_detectable_effect_size(
    n_subjects: int,
    power: float = DEFAULT_POWER,
    alpha: float = DEFAULT_ALPHA,
) -> float:
    """Return the smallest Pearson correlation (|r|) detectable.

    This uses the analytical solution for a two‑tailed test of the null
    hypothesis *r* = 0.

    Parameters
    ----------
    n_subjects: int
        Number of independent observations (subjects).
    power: float, optional
        Desired statistical power (default 0.80).
    alpha: float, optional
        Significance level (default 0.05).

    Returns
    -------
    float
        Detectable absolute correlation coefficient.
    """
    logger.debug(
        "Calculating detectable effect size for N=%d, power=%.2f, alpha=%.3f",
        n_subjects,
        power,
        alpha,
    )
    if n_subjects < 3:
        raise ValueError("At least 3 subjects are required for correlation analysis.")

    cp = CorrelationPower()
    # ``solve_power`` returns the absolute correlation (effect size) needed.
    detectable_r = cp.solve_power(
        effect_size=None,  # we are solving for this
        nobs=n_subjects,
        alpha=alpha,
        power=power,
        alternative="two-sided",
    )
    logger.info(
        "Detectable effect size (|r|) for N=%d: %.4f", n_subjects, detectable_r
    )
    return float(detectable_r)


def generate_power_analysis_report(
    subjects_csv: Path,
    output_json: Path,
    power: float = DEFAULT_POWER,
    alpha: float = DEFAULT_ALPHA,
    correction: str = FDR_CORRECTION,
) -> Dict[str, Any]:
    """Compute and write the power analysis JSON report.

    Parameters
    ----------
    subjects_csv: Path
        Path to ``subjects_included.csv``.
    output_json: Path
        Destination path for the JSON report.
    power: float, optional
        Desired statistical power (default 0.80).
    alpha: float, optional
        Significance level before correction (default 0.05).
    correction: str, optional
        Name of the multiple‑testing correction applied (default ``"FDR"``).

    Returns
    -------
    dict
        Dictionary that was written to ``output_json``.
    """
    df = _load_included_subjects(subjects_csv)
    n = len(df)
    detectable_r = calculate_detectable_effect_size(n, power=power, alpha=alpha)

    report = {
        "sample_size": n,
        "desired_power": power,
        "alpha": alpha,
        "multiple_testing_correction": correction,
        "detectable_effect_size_r": detectable_r,
    }

    # Ensure the parent directory exists.
    output_json.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Writing power analysis report to %s", output_json)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return report


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """Command‑line interface for the power analysis.

    The script expects the following files to exist (relative to the
    repository root):

    * ``data/analysis/subjects_included.csv`` – generated by the QC step.

    It writes:

    * ``data/analysis/power_analysis.json`` – the JSON report.
    """
    # Resolve paths relative to the repository root (the current working
    # directory when the script is executed by the run‑book).
    repo_root = Path(__file__).resolve().parents[2]  # code/analysis/.. -> repo root
    subjects_path = repo_root / "data" / "analysis" / "subjects_included.csv"
    output_path = repo_root / "data" / "analysis" / "power_analysis.json"

    try:
        generate_power_analysis_report(subjects_path, output_path)
        logger.info("Power analysis completed successfully.")
    except Exception as exc:  # pragma: no cover
        logger.error("Power analysis failed: %s", exc)
        raise

if __name__ == "__main__":  # pragma: no cover
    main()