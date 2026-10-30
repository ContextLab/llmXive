"""
Validation script for proxy‑construct validation.

This script computes the Pearson correlation between the weekly
usage metric ``usage_frequency`` (derived from AI‑companion interaction
logs) and the Parasocial Interaction Scale (PIS) scores for a 30‑user
validation subset.  It writes a YAML report to
``data/validation/proxy_construct_report.yaml`` containing the
correlation coefficient, the p‑value, and a pass/fail flag based on the
thresholds defined in the project specification (r ≥ 0.6 and p < 0.05).

The script is deliberately lightweight: it assumes that the required
artefacts already exist on disk (produced by earlier pipeline steps)
and aborts with a clear error message if they are missing or malformed.
"""

import logging
from pathlib import Path

import pandas as pd
from scipy.stats import pearsonr
import yaml

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
USAGE_METRICS_PATH = paths.processed("usage_metrics.parquet")
PIS_SCORES_PATH = paths.raw("pis_scores.parquet")
REPORT_PATH = paths.validation("proxy_construct_report.yaml")

# Thresholds required by the specification
MIN_R = 0.6
MAX_P = 0.05

logger = get_logger(__name__)

def _load_usage_metrics(path: Path) -> pd.DataFrame:
    """Load the usage‑metrics parquet file."""
    if not path.exists():
        raise FileNotFoundError(f"Usage metrics file not found: {path}")
    df = pd.read_parquet(path, columns=["user_id", "usage_frequency"])
    if {"user_id", "usage_frequency"}.issubset(df.columns) is False:
        raise ValueError(
            f"Usage metrics must contain 'user_id' and 'usage_frequency' columns"
        )
    logger.debug(f"Loaded {len(df)} usage‑metric rows from {path}")
    return df

def _load_pis_scores(path: Path) -> pd.DataFrame:
    """Load the Parasocial Interaction Scale scores."""
    if not path.exists():
        raise FileNotFoundError(f"PIS scores file not found: {path}")
    df = pd.read_parquet(path, columns=["user_id", "pis_score"])
    if {"user_id", "pis_score"}.issubset(df.columns) is False:
        raise ValueError(
            f"PIS scores must contain 'user_id' and 'pis_score' columns"
        )
    logger.debug(f"Loaded {len(df)} PIS score rows from {path}")
    return df

def _merge_datasets(usage_df: pd.DataFrame, pis_df: pd.DataFrame) -> pd.DataFrame:
    """Inner‑join the two dataframes on ``user_id``."""
    merged = pd.merge(
        usage_df,
        pis_df,
        on="user_id",
        how="inner",
    )
    if merged.empty:
        raise RuntimeError("No overlapping user IDs between usage metrics and PIS scores")
    logger.info(
        f"Merged datasets: {len(merged)} users with both usage and PIS data"
    )
    return merged

def _compute_correlation(df: pd.DataFrame) -> tuple[float, float]:
    """
    Compute Pearson r and two‑tailed p‑value between ``usage_frequency``
    and ``pis_score``.
    """
    r, p = pearsonr(df["usage_frequency"], df["pis_score"])
    logger.info(f"Pearson r = {r:.4f}, p = {p:.4g}")
    return r, p

def _write_report(report_path: Path, r: float, p: float) -> None:
    """Write the YAML validation report."""
    report = {
        "r": round(r, 4),
        "p_value": round(p, 6),
        "pass": (r >= MIN_R) and (p < MAX_P),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        yaml.dump(report, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Proxy‑construct validation report written to {report_path}")

def main() -> int:
    """
    Entry‑point used by developers and the test suite.

    Returns:
        0 on success, 1 on failure (matching the convention used
        throughout the project).
    """
    try:
        usage_df = _load_usage_metrics(USAGE_METRICS_PATH)
        pis_df = _load_pis_scores(PIS_SCORES_PATH)
        merged_df = _merge_datasets(usage_df, pis_df)

        r, p = _compute_correlation(merged_df)

        _write_report(REPORT_PATH, r, p)

        if r < MIN_R or p >= MAX_P:
            logger.error(
                "Proxy Validation Failed: correlation below threshold "
                f"(r={r:.4f} < {MIN_R}, p={p:.4g} >= {MAX_P})"
            )
            raise RuntimeError("Proxy Validation Failed")
        return 0
    except Exception as exc:
        logger.exception("Proxy‑construct validation encountered an error")
        print(f"Validation failed: {exc}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
