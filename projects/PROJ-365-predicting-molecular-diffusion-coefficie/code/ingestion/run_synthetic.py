"""
Synthetic Data Generation Script (T007b)

This script is invoked when the real diffusion dataset cannot be
downloaded (see T000c). It generates a synthetic dataset using the
existing `generate_synthetic_dataset` utility and records a
`data_source_flag.json` artifact indicating that the data source is
synthetic. The generated CSV is placed under `data/raw/dataset.csv`,
matching the expectations of downstream ingestion steps.
"""

import json
from pathlib import Path

# Project utilities
from utils.config import get_project_root
from create_raw_dir import ensure_raw_dir

# Synthetic data generator (already part of the codebase)
from ingestion.generate_synthetic import generate_synthetic_dataset


def main() -> None:
    """
    Generate a synthetic diffusion dataset and write the source flag.

    The function performs the following steps:
    1. Ensure the ``data/raw`` directory exists.
    2. Generate a CSV file named ``dataset.csv`` inside that directory.
    3. Create ``data/data_source_flag.json`` with ``{"source": "synthetic"}``.
    """
    # 1. Ensure raw data directory exists
    raw_dir: Path = ensure_raw_dir()
    raw_dir.mkdir(parents=True, exist_ok=True)

    # 2. Generate synthetic dataset
    synthetic_csv_path = raw_dir / "dataset.csv"
    generate_synthetic_dataset(synthetic_csv_path)

    # 3. Write the data source flag
    flag_path = Path(get_project_root()) / "data" / "data_source_flag.json"
    flag_path.parent.mkdir(parents=True, exist_ok=True)
    with flag_path.open("w", encoding="utf-8") as fp:
        json.dump({"source": "synthetic"}, fp, indent=2)

    # Inform the user
    print(f"Synthetic dataset written to: {synthetic_csv_path}")
    print(f"Data source flag written to: {flag_path}")


if __name__ == "__main__":
    main()