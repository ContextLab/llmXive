"""
Thin demo pipeline for T003.

Generates a small synthetic validation dataset (10 users × 5 tracks) with
hand‑crafted birth years and track release years so that the true
``adolescent_exposure_ratio`` is known exactly. The pipeline then:

1. Writes ``data/processed/ingested_cohort.parquet`` – the raw synthetic
   cohort.
2. Computes the exposure ratio and writes
   ``data/processed/user_track_pairs.parquet`` – the analysis dataset.
3. Fits a simple linear model (mean_vividness ~ exposure_ratio + popularity)
   and writes ``data/final/regression_summary.csv`` with columns required
   by ``contracts/output.schema.yaml``.

All random seeds are fixed to guarantee reproducibility (required by
SC‑001 and Constitution Principle I).
"""

import csv
import logging
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import statsmodels.api as sm

# ----------------------------------------------------------------------
# Compatibility shim for environments where ``pyarrow`` lacks ``__version__``
# (pandas' compatibility layer expects it).  We only need the attribute
# for the import to succeed; the actual version string is irrelevant here.
# ----------------------------------------------------------------------
if not hasattr(pa, "__version__"):
    pa.__version__ = "0.0.0"

from config import get_project_root
from utils import get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper: write a list‑of‑dicts to a Parquet file using PyArrow.
# ----------------------------------------------------------------------
def _write_parquet(records: list[dict], path: Path) -> None:
    """
    Write ``records`` (a list of dictionaries with uniform keys) to
    ``path`` as a Parquet file.  The function creates parent directories
    as needed.
    """
    if not records:
        raise ValueError("No records to write.")
    table = pa.Table.from_pydict({k: [r[k] for r in records] for k in records[0]})
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path)
    log.info(f"Wrote Parquet file with {len(records)} rows to {path}")

# ----------------------------------------------------------------------
# 1. Synthetic cohort generation
# ----------------------------------------------------------------------
def _generate_synthetic_cohort() -> list[dict]:
    """
    Create a synthetic cohort with 10 users and 5 tracks per user.
    Each user has a birth year; the first two tracks fall within the
    adolescent window (birth_year + 10 … birth_year + 19), giving a known
    exposure ratio of 0.4 for every user.
    """
    np.random.seed(42)

    n_users = 10
    n_tracks = 5

    users = [f"user_{i}" for i in range(n_users)]
    birth_years = np.random.randint(1970, 2000, size=n_users)

    tracks = [f"track_{i}" for i in range(n_tracks)]

    records = []
    for u_idx, user in enumerate(users):
        by = int(birth_years[u_idx])
        # Release years: first two are adolescent, the rest are adult
        release_years = [
            by + 10,  # adolescent
            by + 11,  # adolescent
            by + 30,  # adult
            by + 31,  # adult
            by + 32,  # adult
        ]
        # Random popularity per track (0‑100)
        popularity = np.random.uniform(0, 100, size=n_tracks)

        for t_idx, track in enumerate(tracks):
            records.append(
                {
                    "user_id": user,
                    "birth_year": by,
                    "track_id": track,
                    "release_year": release_years[t_idx],
                    "popularity": float(popularity[t_idx]),
                    "total_listens": 10,  # constant for simplicity
                    "mean_vividness": float(
                        np.random.normal(
                            loc=50 + 0.5 * popularity[t_idx],
                            scale=5.0,
                        )
                    ),
                }
            )
    return records

# ----------------------------------------------------------------------
# 2. Compute adolescent exposure ratio per user
# ----------------------------------------------------------------------
def _compute_exposure(cohort: list[dict]) -> list[dict]:
    """
    Aggregate the raw cohort to user‑level rows and compute the
    ``adolescent_exposure_ratio``.
    """
    # Group by user_id
    users = {}
    for row in cohort:
        uid = row["user_id"]
        if uid not in users:
            users[uid] = {
                "birth_year": row["birth_year"],
                "adolescent_tracks": 0,
                "total_tracks": 0,
                "vividness_sum": 0.0,
                "popularity_sum": 0.0,
            }
        # Determine if this track falls in the adolescent window
        adol_start = row["birth_year"] + 10
        adol_end = row["birth_year"] + 19
        is_adol = int(adol_start <= row["release_year"] <= adol_end)

        users[uid]["adolescent_tracks"] += is_adol
        users[uid]["total_tracks"] += 1
        users[uid]["vividness_sum"] += row["mean_vividness"]
        users[uid]["popularity_sum"] += row["popularity"]

    # Build aggregated records
    agg_records = []
    for uid, stats in users.items():
        agg_records.append(
            {
                "user_id": uid,
                "birth_year": stats["birth_year"],
                "adolescent_exposure_ratio": stats["adolescent_tracks"]
                / stats["total_tracks"],
                "mean_vividness": stats["vividness_sum"] / stats["total_tracks"],
                "popularity": stats["popularity_sum"] / stats["total_tracks"],
            }
        )
    return agg_records

# ----------------------------------------------------------------------
# 3. Fit a simple linear regression model and write a CSV summary
# ----------------------------------------------------------------------
def _fit_and_save_model(pairs: list[dict], out_path: Path) -> None:
    """
    Fit ``mean_vividness ~ adolescent_exposure_ratio + popularity`` using
    OLS (no random effects – sufficient for the thin demo).  The resulting
    CSV contains the columns required by ``contracts/output.schema.yaml``:

    term, estimate, std_error, t_value, p_value, vif
    """
    # Prepare design matrix
    X = np.column_stack(
        [
            np.ones(len(pairs)),  # intercept
            [r["adolescent_exposure_ratio"] for r in pairs],
            [r["popularity"] for r in pairs],
        ]
    )
    y = np.array([r["mean_vividness"] for r in pairs])

    # Fit OLS
    model = sm.OLS(y, X).fit()

    # Extract coefficient table (skip intercept for VIF)
    terms = ["intercept", "adolescent_exposure_ratio", "popularity"]
    estimates = model.params
    std_err = model.bse
    t_vals = model.tvalues
    p_vals = model.pvalues

    # Compute VIF for the two predictors (intercept excluded)
    # VIF = 1 / (1 - R^2) of regressing each predictor on the others
    # Using the standard formula via statsmodels
    from statsmodels.stats.outliers_influence import variance_inflation_factor

    vif_vals = {}
    for i, term in enumerate(terms):
        if term == "intercept":
            vif_vals[term] = float("nan")
        else:
            # variance_inflation_factor expects the full design matrix
            vif_vals[term] = variance_inflation_factor(X, i)

    # Write CSV with required column names
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            ["term", "estimate", "std_error", "t_value", "p_value", "vif"]
        )
        for i, term in enumerate(terms):
            writer.writerow(
                [
                    term,
                    estimates[i],
                    std_err[i],
                    t_vals[i],
                    p_vals[i],
                    vif_vals[term],
                ]
            )
    log.info(f"Regression summary written to {out_path}")

# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def main() -> None:
    """
    Orchestrate the thin synthetic pipeline:

    * Generate the raw synthetic cohort.
    * Persist ``ingested_cohort.parquet``.
    * Compute exposure ratio and persist ``user_track_pairs.parquet``.
    * Fit the regression model and persist ``regression_summary.csv``.
    """
    project_root = get_project_root()

    # Define artifact paths
    ingested_path = (
        project_root / "data" / "processed" / "ingested_cohort.parquet"
    )
    pairs_path = (
        project_root / "data" / "processed" / "user_track_pairs.parquet"
    )
    summary_path = (
        project_root / "data" / "final" / "regression_summary.csv"
    )

    # 1. Generate synthetic cohort
    log.info("Generating synthetic cohort...")
    cohort_records = _generate_synthetic_cohort()
    _write_parquet(cohort_records, ingested_path)

    # 2. Compute exposure ratio and write user‑track pairs
    log.info("Computing adolescent exposure ratio...")
    pair_records = _compute_exposure(cohort_records)
    _write_parquet(pair_records, pairs_path)

    # 3. Fit model and write regression summary
    log.info("Fitting linear model...")
    _fit_and_save_model(pair_records, summary_path)

    log.info("Thin demo pipeline completed successfully.")


if __name__ == "__main__":
    main()
