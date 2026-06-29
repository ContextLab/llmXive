"""
Validation module: Compute convergent (Pearson) correlation between
computed agency scores and an external perceived‑agency scale.
Includes detailed logging and warnings for threshold violations (FR‑008).
"""
from __future__ import annotations

import pathlib
from typing import Tuple

import pandas as pd
from scipy import stats

from logging.pipeline_logger import get_logger, log_dict

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
CORRELATION_THRESHOLD = 0.30  # Minimum acceptable Pearson r
P_VALUE_THRESHOLD = 0.05

# ----------------------------------------------------------------------
# Logger
# ----------------------------------------------------------------------
_logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def compute_convergent_correlation(
    merged_data_path: pathlib.Path,
) -> Tuple[float, float]:
    """
    Compute Pearson correlation between agency scores and external scale.

    Parameters
    ----------
    merged_data_path: pathlib.Path
        CSV file containing at least two columns:
        ``agency_score`` and ``external_scale_score``.

    Returns
    -------
    Tuple[float, float]
        (r, p_value) of the Pearson correlation.
    """
    _logger.info("Starting convergent validity computation.")
    try:
        df = pd.read_csv(merged_data_path)
        _logger.debug(
            f"Loaded merged data with shape {df.shape} from {merged_data_path}."
        )
    except Exception as exc:
        _logger.error(f"Failed to read merged data: {exc}")
        raise

    required = {"agency_score", "external_scale_score"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        _logger.error(f"Missing required columns for correlation: {missing}")
        raise ValueError(f"Missing columns: {missing}")

    # Drop rows with NaNs in either column
    clean_df = df.dropna(subset=["agency_score", "external_scale_score"])
    _logger.debug(f"Rows after NaN removal: {clean_df.shape[0]}")

    if clean_df.empty:
        _logger.warning("No data available after NaN removal; returning NaN.")
        return float("nan"), float("nan")

    r, p = stats.pearsonr(
        clean_df["agency_score"], clean_df["external_scale_score"]
    )
    log_dict(
        {
            "event": "convergent_correlation_computed",
            "pearson_r": r,
            "p_value": p,
            "data_path": str(merged_data_path),
        }
    )
    _logger.info(
        f"Pearson r = {r:.4f}, p‑value = {p:.4g} (thresholds: r≥{CORRELATION_THRESHOLD}, p<={P_VALUE_THRESHOLD})"
    )

    if r < CORRELATION_THRESHOLD or p > P_VALUE_THRESHOLD:
        _logger.warning(
            f"Convergent validity not met (r={r:.4f}, p={p:.4g})."
        )
    return float(r), float(p)

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def parse_args() -> pathlib.Path:
    """Parse command‑line arguments and return path to merged data CSV."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Compute convergent validity (Pearson correlation)."
    )
    parser.add_argument(
        "merged_data_path",
        type=pathlib.Path,
        help="Path to CSV containing agency_score and external_scale_score columns.",
    )
    args = parser.parse_args()
    return args.merged_data_path

def main() -> None:
    """CLI entry point."""
    data_path = parse_args()
    r, p = compute_convergent_correlation(data_path)
    print(f"Pearson r = {r:.4f}, p = {p:.4g}")
