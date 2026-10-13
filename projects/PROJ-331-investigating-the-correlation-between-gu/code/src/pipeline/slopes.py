"""Per‑patient slope computation (Task T003).

This module reads the CLR‑transformed abundance table produced by the
preprocessing step and computes, for each patient, the linear slope of
each taxon abundance over time (in years).  It also computes the slope of
the longitudinal clinical outcome ``MDS_UPDRS_Total`` when that column is
present.  The results are written to parquet files under
``data/processed/``.

Output files:
  - data/processed/patient_taxon_slopes.parquet
  - data/processed/patient_outcome_slopes.parquet  (only if outcome present)
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _load_clr(ab_path: Path | None = None) -> pd.DataFrame:
    """Load the CLR‑transformed abundances.

    Parameters
    ----------
    ab_path: optional explicit path; if ``None`` the default location
    ``data/processed/clr_abundances.parquet`` is used.

    Returns
    -------
    pd.DataFrame
        Must contain columns ``patient_id``, ``visit_date`` and one column
        per retained taxon.
    """
    if ab_path is None:
        ab_path = paths.data("processed", "clr_abundances.parquet")
    if not ab_path.is_file():
        raise FileNotFoundError(f"CLR abundances file not found: {ab_path}")
    df = pd.read_parquet(ab_path)
    log.info("Loaded CLR abundances: %d rows, %d columns", len(df), len(df.columns))
    return df


def _load_clinical(clin_path: Path | None = None) -> pd.DataFrame:
    """Load the clinical metadata (may or may not contain the outcome)."""
    if clin_path is None:
        clin_path = paths.data("raw", "ppmi_clinical.parquet")
    if not clin_path.is_file():
        raise FileNotFoundError(f"Clinical metadata file not found: {clin_path}")
    df = pd.read_parquet(clin_path)
    log.info(
        "Loaded clinical metadata: %d rows, %d columns", len(df), len(df.columns)
    )
    return df


def _prepare_time(df: pd.DataFrame) -> pd.DataFrame:
    """Add a ``time_years`` column (float) representing years since first visit."""
    df = df.copy()
    df["visit_date"] = pd.to_datetime(df["visit_date"])
    # Compute offset in days relative to the earliest visit for each patient
    df["time_days"] = df.groupby("patient_id")["visit_date"].transform(
        lambda x: (x - x.min()).dt.total_seconds() / (24 * 3600)
    )
    df["time_years"] = df["time_days"] / 365.25
    return df


def _fit_slope(x: np.ndarray, y: np.ndarray) -> float:
    """Return the slope from a simple linear regression (least‑squares)."""
    if len(x) < 2:
        # Should never happen because we filter patients with <2 visits
        return np.nan
    # np.polyfit returns [slope, intercept] for degree=1
    slope, _ = np.polyfit(x, y, 1)
    return float(slope)


# ----------------------------------------------------------------------
# Core computation
# ----------------------------------------------------------------------


def compute_taxon_slopes(
    clr_df: pd.DataFrame, taxon_columns: List[str] | None = None
) -> pd.DataFrame:
    """Compute per‑patient taxon slopes.

    Parameters
    ----------
    clr_df: DataFrame with CLR abundances and metadata.
    taxon_columns: optional list of taxon columns; if ``None`` all columns
    not in the metadata set are treated as taxa.

    Returns
    -------
    pd.DataFrame
        Long‑format table with columns ``patient_id``, ``taxon_name``,
        ``slope``.
    """
    required_meta = {"patient_id", "visit_date"}
    if not required_meta.issubset(clr_df.columns):
        raise ValueError(
            f"CLR DataFrame must contain columns {required_meta}, got {clr_df.columns}"
        )

    df = _prepare_time(clr_df)

    if taxon_columns is None:
        taxon_columns = [
            c
            for c in df.columns
            if c not in {"sample_id", "patient_id", "visit_date", "time_days", "time_years"}
        ]

    records = []
    for patient_id, group in df.groupby("patient_id"):
        times = group["time_years"].values
        for taxon in taxon_columns:
            values = group[taxon].values
            slope = _fit_slope(times, values)
            records.append(
                {"patient_id": patient_id, "taxon_name": taxon, "slope": slope}
            )
    result = pd.DataFrame.from_records(records)
    log.info(
        "Computed taxon slopes for %d patients and %d taxa",
        df["patient_id"].nunique(),
        len(taxon_columns),
    )
    return result


def compute_outcome_slopes(clinical_df: pd.DataFrame) -> pd.DataFrame:
    """Compute per‑patient slope of ``MDS_UPDRS_Total`` over time.

    Returns a DataFrame with columns ``patient_id`` and ``outcome_slope``.
    """
    if "MDS_UPDRS_Total" not in clinical_df.columns:
        raise ValueError("Outcome column 'MDS_UPDRS_Total' not present in clinical data.")
    df = clinical_df.copy()
    df["visit_date"] = pd.to_datetime(df["visit_date"])
    df["time_days"] = df.groupby("patient_id")["visit_date"].transform(
        lambda x: (x - x.min()).dt.total_seconds() / (24 * 3600)
    )
    df["time_years"] = df["time_days"] / 365.25

    records = []
    for patient_id, group in df.groupby("patient_id"):
        times = group["time_years"].values
        outcomes = group["MDS_UPDRS_Total"].values
        slope = _fit_slope(times, outcomes)
        records.append({"patient_id": patient_id, "outcome_slope": slope})
    result = pd.DataFrame.from_records(records)
    log.info(
        "Computed outcome slopes for %d patients", df["patient_id"].nunique()
    )
    return result


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------


def run_slopes(
    clr_path: Path | None = None,
    clinical_path: Path | None = None,
) -> Tuple[Path, Path | None]:
    """Execute the full slope‑computation phase.

    Writes:
        data/processed/patient_taxon_slopes.parquet
        data/processed/patient_outcome_slopes.parquet  (if outcome present)

    Returns
    -------
    tuple(Path, Path | None)
        Paths to the written parquet files (second element may be ``None``).
    """
    clr_df = _load_clr(clr_path)

    # Determine taxon columns automatically
    taxon_cols = [
        c
        for c in clr_df.columns
        if c
        not in {"sample_id", "patient_id", "visit_date", "time_days", "time_years"}
    ]

    taxon_slopes = compute_taxon_slopes(clr_df, taxon_columns=taxon_cols)

    taxon_out_path = paths.data(
        "processed", "patient_taxon_slopes.parquet"
    )
    taxon_out_path.parent.mkdir(parents=True, exist_ok=True)
    taxon_slopes.to_parquet(taxon_out_path, index=False)
    log.info("Wrote patient taxon slopes to %s", taxon_out_path)

    # Outcome slopes – only if the outcome column exists
    outcome_out_path: Path | None = None
    try:
        clinical_df = _load_clinical(clinical_path)
        if "MDS_UPDRS_Total" in clinical_df.columns:
            outcome_slopes = compute_outcome_slopes(clinical_df)
            outcome_out_path = paths.data(
                "processed", "patient_outcome_slopes.parquet"
            )
            outcome_out_path.parent.mkdir(parents=True, exist_ok=True)
            outcome_slopes.to_parquet(outcome_out_path, index=False)
            log.info(
                "Wrote patient outcome slopes to %s", outcome_out_path
            )
        else:
            log.warning(
                "Outcome column 'MDS_UPDRS_Total' missing – skipping outcome slope computation."
            )
    except FileNotFoundError as exc:
        log.error("Failed to load clinical data for outcome slopes: %s", exc)
        # According to FR‑004 we should skip rather than abort.
    return taxon_out_path, outcome_out_path


def main() -> int:
    """Entry point for ``python -m code.src.pipeline.slopes``."""
    run_slopes()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
