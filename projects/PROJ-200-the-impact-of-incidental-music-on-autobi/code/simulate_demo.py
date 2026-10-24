"""
Thin demo pipeline for T003.

Generates a small synthetic validation dataset (10 users × 5 tracks) with
hand‑crafted birth years and track release years so that the true
``adolescent_exposure_ratio`` is known exactly.  The pipeline then:

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

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from pathlib import Path

from config import get_project_root
from utils import get_logger, write_parquet

log = get_logger(__name__)

def _generate_synthetic_cohort() -> pd.DataFrame:
    """
    Create a synthetic cohort with 10 users and 5 tracks per user.
    Each user has a birth year; two of the five tracks fall within the
    adolescent window (birth_year + 10 … birth_year + 19), giving a known
    exposure ratio of 0.4 for every user‑track pair.
    """
    np.random.seed(42)

    n_users = 10
    n_tracks = 5

    users = [f"user_{i}" for i in range(n_users)]
    birth_years = np.random.randint(1970, 2000, size=n_users)

    # Track identifiers are shared across users for simplicity
    tracks = [f"track_{i}" for i in range(n_tracks)]

    rows = []
    for u_idx, user in enumerate(users):
        by = int(birth_years[u_idx])
        # Define release years: first two are adolescent, others are not
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
            rows.append({
                "user_id": user,
                "birth_year": by,
                "track_id": track,
                "release_year": release_years[t_idx],
                "popularity": popularity[t_idx],
                # For the thin demo we fix total listens to 10 for every pair
                "total_listens": 10,
                # Vividness is a synthetic outcome loosely correlated with
                # exposure and popularity; the exact values are not important
                # for the exposure‑accuracy test.
                "mean_vividness": np.random.normal(
                    loc=50 + 0.5 * popularity[t_idx],
                    scale=5.0
                ),
            })
    return pd.DataFrame(rows)

def _compute_exposure(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute ``adolescent_exposure_ratio`` for each row.
    The adolescent window is ages 10‑19 inclusive.
    """
    # Determine adolescent window bounds per user
    df["adol_start"] = df["birth_year"] + 10
    df["adol_end"] = df["birth_year"] + 19

    # Flag tracks that fall within the window
    df["is_adolescent"] = (
        (df["release_year"] >= df["adol_start"])
        & (df["release_year"] <= df["adol_end"])
    ).astype(int)

    # Since each row represents a single track listen count, the ratio is
    # simply the flag divided by total listens for that track.  Because we
    # set ``total_listens`` to a constant (10) and have exactly one row per
    # track, the ratio reduces to ``is_adolescent / 1`` i.e. 1.0 for the
    # adolescent tracks and 0.0 otherwise.  To obtain the overall exposure
    # ratio per user‑track pair (as required by the spec), we aggregate
    # over the five tracks belonging to the same user.
    agg = (
        df.groupby(["user_id", "birth_year"])
        .agg(
            adolescent_tracks=("is_adolescent", "sum"),
            total_tracks=("track_id", "count"),
            mean_vividness=("mean_vividness", "mean"),
            popularity=("popularity", "mean"),
        )
        .reset_index()
    )
    agg["adolescent_exposure_ratio"] = agg["adolescent_tracks"] / agg["total_tracks"]
    # The expected ratio is 2 / 5 = 0.4 for every user
    return agg

def _fit_model(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fit a simple linear regression model:
        mean_vividness ~ adolescent_exposure_ratio + popularity
    Returns a DataFrame matching the contract schema:
    term, estimate, std_error, t_value, p_value, vif
    """
    # Prepare design matrix
    X = df[["adolescent_exposure_ratio", "popularity"]]
    X = sm.add_constant(X)  # adds intercept term

    y = df["mean_vividness"]
    model = sm.OLS(y, X).fit()

    # Extract basic statistics
    summary = model.summary2().tables[1].reset_index()
    summary = summary.rename(columns={"index": "term"})

    # Compute VIF for the two predictors (excluding the intercept)
    vif_vals = {}
    for col in ["adolescent_exposure_ratio", "popularity"]:
        vif_vals[col] = variance_inflation_factor(
            X[["const", "adolescent_exposure_ratio", "popularity"]].values,
            X.columns.get_loc(col)
        )
    # Map VIFs into the summary; intercept gets NaN
    summary["vif"] = summary["term"].apply(lambda t: vif_vals.get(t, np.nan))

    # Ensure the column order required by the contract
    summary = summary[
        ["term", "Coef.", "Std.Err.", "t", "P>|t|", "vif"]
    ].rename(
        columns={
            "Coef.": "estimate",
            "Std.Err.": "std_error",
            "t": "t_value",
            "P>|t|": "p_value",
        }
    )
    return summary

def main() -> None:
    """
    Orchestrate the thin synthetic pipeline:

    * Generate the raw synthetic cohort.
    * Persist ``ingested_cohort.parquet``.
    * Compute exposure ratio and persist ``user_track_pairs.parquet``.
    * Fit the regression model and persist ``regression_summary.csv``.
    """
    project_root = get_project_root()

    # Paths for artifacts
    ingested_path = project_root / "data" / "processed" / "ingested_cohort.parquet"
    pairs_path = project_root / "data" / "processed" / "user_track_pairs.parquet"
    summary_path = project_root / "data" / "final" / "regression_summary.csv"

    # 1. Synthetic cohort generation
    log.info("Generating synthetic cohort...")
    cohort_df = _generate_synthetic_cohort()
    write_parquet(cohort_df, ingested_path)
    log.info(f"Synthetic ingested cohort written to {ingested_path}")

    # 2. Compute exposure ratio and write user‑track pairs
    log.info("Computing adolescent exposure ratio...")
    pairs_df = _compute_exposure(cohort_df)
    write_parquet(pairs_df, pairs_path)
    log.info(f"User‑track pair dataset written to {pairs_path}")

    # 3. Fit model and write regression summary
    log.info("Fitting linear model...")
    summary_df = _fit_model(pairs_df)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(summary_path, index=False)
    log.info(f"Regression summary written to {summary_path}")

if __name__ == "__main__":
    main()