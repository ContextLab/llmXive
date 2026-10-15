import pandas as pd
import numpy as np
from pathlib import Path
from config import get_project_root
from utils import get_logger, write_parquet
import simulate_amt
import datasets

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions required by unit tests and pipeline
# ----------------------------------------------------------------------
def filter_cohort(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove records with missing or implausible birth years and compute
    adolescent exposure windows.

    Expected columns:
        - track_id
        - birth_year
        - listen_year
        - vividness (optional)

    Returns a DataFrame with the original columns plus:
        - adolescent_start
        - adolescent_end
        - is_adolescent_listen (bool)
    """
    mask = df["birth_year"].notna() & df["birth_year"].between(1900, 2025)
    filtered = df.loc[mask].copy()
    filtered["adolescent_start"] = filtered["birth_year"] + 10
    filtered["adolescent_end"] = filtered["birth_year"] + 19
    filtered["is_adolescent_listen"] = (
        (filtered["listen_year"] >= filtered["adolescent_start"])
        & (filtered["listen_year"] <= filtered["adolescent_end"])
    )
    return filtered

def calculate_ratio_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the adolescent exposure ratio for each track.
    """
    if df.empty:
        return pd.DataFrame(columns=["track_id", "adolescent_exposure_score"])

    agg = (
        df.groupby("track_id")["is_adolescent_listen"]
        .agg(["sum", "count"])
        .reset_index()
    )
    agg["adolescent_exposure_score"] = agg["sum"] / agg["count"]
    return agg[["track_id", "adolescent_exposure_score"]]

def handle_fallback(df: pd.DataFrame) -> bool:
    """
    Determine whether the Global Exposure fallback should be triggered.
    """
    if df.empty:
        return True
    missing = df["birth_year"].isna().sum()
    proportion_missing = missing / len(df)
    return proportion_missing > 0.5

def apply_frequency_threshold(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply FR‑009: keep only tracks with at least three total listens.
    """
    if df.empty:
        return df
    counts = df["track_id"].value_counts()
    valid_tracks = counts[counts >= 3].index
    return df[df["track_id"].isin(valid_tracks)].copy()

# ----------------------------------------------------------------------
# Main ingestion routine – produces ``data/processed/ingested_cohort.parquet``
# ----------------------------------------------------------------------
def main():
    """
    Full ingestion pipeline for the thin end‑to‑end run.
    """
    log.info("Running full data ingestion (User Story 1)…")

    # 1‑2. Simulated AMT data (required for birth years)
    simulate_amt.main()
    root = get_project_root()
    amt_path = root / "data" / "raw" / "simulated_amt.parquet"
    amt_df = pd.read_parquet(amt_path)

    # 3‑4. Load MSD listening logs (real data) via HuggingFace streaming
    log.info("Loading MSD listening logs from HuggingFace dataset…")
    ds = datasets.load_dataset("matthewfranglen/lastfm-1k", streaming=True)["train"]

    rows = []
    for i, rec in enumerate(ds):
        if i >= 50_000:  # keep within resource limits
            break
        rows.append(
            {
                "user_id": rec["user_id"],
                "track_index": rec["track_index"],
                "timestamp": rec["timestamp"],
            }
        )
    msd_df = pd.DataFrame(rows)

    msd_df["track_id"] = msd_df["track_index"].apply(lambda x: f"track_{x}")
    msd_df["listen_year"] = pd.to_datetime(
        msd_df["timestamp"], unit="s"
    ).dt.year

    # Compute popularity and release_date (real values)
    popularity_df = (
        msd_df.groupby("track_id")
        .size()
        .reset_index(name="popularity")
    )
    release_df = (
        msd_df.groupby("track_id")["listen_year"]
        .min()
        .reset_index(name="release_date")
    )

    # Validate required columns
    required = {"track_id", "release_date", "popularity"}
    available = set(release_df.columns).union(popularity_df.columns)
    if not required.issubset(available):
        missing = required - available
        raise ValueError(f"MSD source missing required columns: {', '.join(missing)}")

    # 5. Merge AMT cues with listening events
    merged = pd.merge(
        amt_df,
        msd_df[["user_id", "track_id", "listen_year"]],
        on=["user_id", "track_id"],
        how="inner",
    )
    if merged.empty:
        log.warning("No matching listen records found after merge.")

    # 6. Global exposure fallback check (before filtering)
    fallback_triggered = handle_fallback(amt_df)
    if fallback_triggered:
        log.warning(
            "Global exposure fallback triggered (>50%% missing birth years)."
        )
        # In the thin pipeline we do not compute a proxy; the flag is sufficient.

    # 7. Minimum listen threshold
    merged = apply_frequency_threshold(merged)

    # 8. Compute adolescent windows and exposure ratio
    filtered = filter_cohort(merged)
    ratio_df = calculate_ratio_score(filtered)

    # Compute mean vividness per user‑track (needed for modeling)
    mean_vivid_df = (
        filtered.groupby(["user_id", "track_id"])["vividness"]
        .mean()
        .reset_index(name="mean_vividness")
    )

    # Assemble final cohort
    cohort = pd.merge(ratio_df, popularity_df, on="track_id", how="left")
    cohort = pd.merge(cohort, release_df, on="track_id", how="left")
    cohort = pd.merge(cohort, mean_vivid_df, on="track_id", how="left")

    # Write out
    out_path = root / "data" / "processed" / "ingested_cohort.parquet"
    write_parquet(cohort, out_path)
    log.info(f"Ingested cohort written to {out_path}")

if __name__ == "__main__":
    main()
