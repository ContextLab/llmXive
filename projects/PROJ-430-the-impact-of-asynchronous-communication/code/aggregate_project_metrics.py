"""
Aggregation script to compute project-level metrics from pair-level metrics.
Implements the mandatory aggregation logic for T015:
- median of response_time_variance per project
- mean of mean_delay per project
- team size (unique contributors) per project
- project age (days between first and last event) per project
Output is written to `data/derived/project_metrics.csv`.
"""
import argparse
import json
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd

from config import get_config, ensure_directories_exist
from utils.logger import get_logger

logger = get_logger(__name__)

def load_pair_metrics(parquet_path: Path) -> pd.DataFrame:
    """Load pair‑level metrics from a parquet file."""
    if not parquet_path.exists():
        logger.error(f"Pair metrics file not found: {parquet_path}")
        raise FileNotFoundError(parquet_path)
    df = pd.read_parquet(parquet_path)
    required = {"project_id", "response_time_variance", "mean_delay", "pair_id"}
    missing = required - set(df.columns)
    if missing:
        logger.error(f"Pair metrics missing columns: {missing}")
        raise ValueError(f"Missing columns in pair metrics: {missing}")
    return df

def load_raw_events(json_path: Path) -> pd.DataFrame:
    """Load raw events JSON and return a DataFrame with minimal needed columns."""
    if not json_path.exists():
        logger.error(f"Raw events file not found: {json_path}")
        raise FileNotFoundError(json_path)
    with open(json_path, "r", encoding="utf-8") as f:
        events = json.load(f)
    if not isinstance(events, list):
        logger.error("Raw events JSON does not contain a list.")
        raise ValueError("Invalid events JSON structure.")
    df = pd.DataFrame(events)
    # Expected columns: project_id, author_id (or actor.login), created_at
    # Normalise column names to a common schema
    if "author_id" not in df.columns:
        # Try to infer author identifier from the actor dict
        if "actor" in df.columns:
            df["author_id"] = df["actor"].apply(lambda x: x.get("login") if isinstance(x, dict) else None)
        else:
            logger.error("Cannot determine author identifier in raw events.")
            raise ValueError("Missing author identifier.")
    if "created_at" not in df.columns:
        logger.error("Missing timestamp column 'created_at' in raw events.")
        raise ValueError("Missing timestamp.")
    return df[["project_id", "author_id", "created_at"]]

def compute_team_size(df_events: pd.DataFrame) -> pd.Series:
    """Return a Series indexed by project_id with the number of unique contributors."""
    team_sizes = df_events.groupby("project_id")["author_id"].nunique()
    return team_sizes

def compute_project_age(df_events: pd.DataFrame) -> pd.Series:
    """Return a Series indexed by project_id with age in days (max - min timestamp)."""
    # Convert timestamps to pandas datetime
    df_events["ts"] = pd.to_datetime(df_events["created_at"], utc=True, errors="coerce")
    # Drop rows where timestamp could not be parsed
    df_clean = df_events.dropna(subset=["ts"])
    age_days = (
        df_clean.groupby("project_id")["ts"]
        .agg(lambda x: (x.max() - x.min()).days)
    )
    return age_days

def aggregate_project_metrics(pair_df: pd.DataFrame,
                              events_df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform the required aggregation and return a DataFrame ready for CSV export.
    Columns:
      - project_id
      - median_variance
      - mean_delay
      - team_size
      - project_age
    """
    # Median variance per project
    median_variance = pair_df.groupby("project_id")["response_time_variance"].median()
    # Mean of mean_delay per project
    mean_delay = pair_df.groupby("project_id")["mean_delay"].mean()

    # Team size and project age from raw events
    team_size = compute_team_size(events_df)
    project_age = compute_project_age(events_df)

    # Combine into a single DataFrame
    agg_df = pd.concat(
        [median_variance, mean_delay, team_size, project_age],
        axis=1,
        keys=["median_variance", "mean_delay", "team_size", "project_age"]
    ).reset_index()

    # Ensure correct dtypes
    agg_df["median_variance"] = agg_df["median_variance"].astype(float)
    agg_df["mean_delay"] = agg_df["mean_delay"].astype(float)
    agg_df["team_size"] = agg_df["team_size"].astype(int)
    agg_df["project_age"] = agg_df["project_age"].astype(int)

    return agg_df

def main():
    parser = argparse.ArgumentParser(
        description="Aggregate pair‑level metrics to project‑level metrics (T015)."
    )
    parser.add_argument(
        "--pair-metrics",
        type=str,
        default=None,
        help="Path to pair‑level metrics parquet file. "
             "If omitted, uses config-derived default."
    )
    parser.add_argument(
        "--raw-events",
        type=str,
        default=None,
        help="Path to raw events JSON file. "
             "If omitted, uses config-derived default."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to write project‑level CSV. "
             "If omitted, uses config‑derived default."
    )
    args = parser.parse_args()

    cfg = get_config()
    ensure_directories_exist(cfg)

    # Resolve default paths from config
    pair_path = Path(args.pair_metrics) if args.pair_metrics else Path(cfg.get("derived_dir", "data/derived")) / "pair_metrics.parquet"
    raw_path = Path(args.raw_events) if args.raw_events else Path(cfg.get("raw_dir", "data/raw")) / "events.json"
    out_path = Path(args.output) if args.output else Path(cfg.get("derived_dir", "data/derived")) / "project_metrics.csv"

    logger.info(f"Loading pair metrics from {pair_path}")
    pair_df = load_pair_metrics(pair_path)

    logger.info(f"Loading raw events from {raw_path}")
    events_df = load_raw_events(raw_path)

    logger.info("Aggregating project‑level metrics")
    project_df = aggregate_project_metrics(pair_df, events_df)

    # Ensure output directory exists
    out_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing project metrics to {out_path}")
    project_df.to_csv(out_path, index=False)

    logger.info("Aggregation complete.")

if __name__ == "__main__":
    main()
