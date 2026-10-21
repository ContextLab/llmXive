"""
Minimal dataset downloader for the checkpointing task.

This script downloads a single small, public dataset (OpenML Iris dataset,
ID 61) and stores it under ``data/raw`` as a parquet file.  It also creates
a minimal ``data/datasets.csv`` entry so that the downstream checksum stage
can operate without requiring the full download implementation that will be
added in later tasks.
"""
import logging
import sys
from pathlib import Path

import pandas as pd
from sklearn.datasets import fetch_openml

def _ensure_datasets_csv(csv_path: Path) -> None:
    """Create the datasets CSV with a header if it does not exist."""
    if not csv_path.exists():
        header = (
            "dataset_id,source_url,sample_size,num_variables,"
            "continuous_variables,checksum,skewness,kurtosis,included\n"
        )
        csv_path.write_text(header)

def main() -> None:
    """Download a single OpenML dataset and record minimal metadata."""
    logger = logging.getLogger("download")
    logger.setLevel(logging.INFO)

    data_dir = Path("data")
    raw_dir = data_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    datasets_csv = data_dir / "datasets.csv"
    _ensure_datasets_csv(datasets_csv)

    # ------------------------------------------------------------
    # 1️⃣  Download the Iris dataset (OpenML ID 61)
    # ------------------------------------------------------------
    dataset_id = "61"
    source_url = f"https://www.openml.org/d/{dataset_id}"
    logger.info(f"Downloading OpenML dataset {dataset_id} from {source_url}")

    try:
        oml = fetch_openml(data_id=dataset_id, as_frame=True, parser="auto")
    except Exception as exc:  # pragma: no cover – should not happen in CI
        logger.error(f"Failed to download OpenML dataset {dataset_id}: {exc}")
        sys.exit(1)

    df: pd.DataFrame = oml.frame

    # ------------------------------------------------------------
    # 2️⃣  Persist the raw data as parquet
    # ------------------------------------------------------------
    out_path = raw_dir / f"openml_{dataset_id}.parquet"
    df.to_parquet(out_path)
    logger.info(f"Wrote raw parquet to {out_path}")

    # ------------------------------------------------------------
    # 3️⃣  Append a minimal metadata row to ``datasets.csv``
    # ------------------------------------------------------------
    sample_size = len(df)
    num_variables = df.shape[1]
    continuous_vars = df.select_dtypes(include="number").shape[1]

    # The checksum, skewness, kurtosis, and inclusion flag will be filled
    # later by the checksum and filtering stages.
    with datasets_csv.open("a", newline="") as f:
        f.write(
            f"{dataset_id},{source_url},{sample_size},{num_variables},"
            f"{continuous_vars},,,,\n"
        )
    logger.info("Appended minimal metadata to data/datasets.csv")

if __name__ == "__main__":
    main()
