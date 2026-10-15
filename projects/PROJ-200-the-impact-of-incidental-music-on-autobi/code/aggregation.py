"""
Thin aggregation step for T003.

The purpose of this script is to transform the ingested cohort produced
by ``code/data_ingestion.py`` into the ``user_track_pairs.parquet`` file
expected by downstream analysis.  For the thin pipeline we simply pass
through the data, keeping the columns required by the regression model.
"""

import logging
from pathlib import Path

import pandas as pd

from config import get_project_root
from utils import get_logger, write_parquet

logger = get_logger(__name__)

def main() -> None:
    """
    Read the ingested cohort, perform minimal aggregation, and write the
    ``user_track_pairs.parquet`` artifact.

    The ingested cohort already contains:
        - user_id
        - track_id
        - adolescent_exposure_score
        - popularity
        - mean_vividness
    We simply ensure the column names match the contract and write the
    result to the processed folder.
    """
    root = get_project_root()
    ingested_path = root / "data" / "processed" / "ingested_cohort.parquet"
    output_path = root / "data" / "processed" / "user_track_pairs.parquet"

    logger.info(f"Loading ingested cohort from {ingested_path}")
    df = pd.read_parquet(ingested_path)

    # Verify required columns exist; raise a clear error if not.
    required = {
        "user_id",
        "track_id",
        "adolescent_exposure_score",
        "popularity",
        "mean_vividness",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Ingested cohort is missing required columns for aggregation: {missing}"
        )

    # For the thin pipeline we do not perform additional aggregation.
    # Ensure column order is deterministic for downstream tests.
    df = df[
        [
            "user_id",
            "track_id",
            "adolescent_exposure_score",
            "popularity",
            "mean_vividness",
        ]
    ].copy()

    logger.info(f"Writing user‑track pair dataset to {output_path}")
    write_parquet(df, output_path)

    logger.info("Aggregation step completed successfully.")

if __name__ == "__main__":
    main()
