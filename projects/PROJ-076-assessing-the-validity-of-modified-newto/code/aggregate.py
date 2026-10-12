"""
Aggregation helper for T015.

The original implementation was a stub; this version provides concrete
functionality used by ``code/preprocess.py`` to update the metadata file
after the filtered CSV has been written.
"""

import os
import logging
import pandas as pd
import yaml
from pathlib import Path
from datetime import datetime

__all__ = ["load_filtered_data", "update_metadata", "main"]

def load_filtered_data(input_path: str) -> pd.DataFrame:
    """
    Load the filtered galaxy CSV produced by ``code/preprocess.py``.

    Parameters
    ----------
    input_path : str
        Path to the CSV file.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing the filtered data.

    Raises
    ------
    FileNotFoundError
        If the CSV does not exist.
    ValueError
        If the file is empty.
    """
    path = Path(input_path)
    if not path.is_file():
        raise FileNotFoundError(f"Filtered data not found: {input_path}")

    df = pd.read_csv(path)
    if df.empty:
        raise ValueError(f"Filtered data file is empty: {input_path}")

    return df

def update_metadata(
    metadata_path: str,
    output_path: str,
    timestamp: str,
    version: str = "1.1",
) -> None:
    """
    Update ``data/metadata.yaml`` with processing information.

    Parameters
    ----------
    metadata_path : str
        Path to the existing ``metadata.yaml`` file.
    output_path : str
        Path to the newly created ``filtered_galaxies.csv``.
    timestamp : str
        ISO‑8601 timestamp indicating when the file was generated.
    version : str, optional
        Version identifier for the processed dataset. Defaults to ``"1.1"``.
    """
    meta_path = Path(metadata_path)
    # Load (or create) the metadata structure
    if meta_path.is_file():
        with meta_path.open("r", encoding="utf-8") as f:
            meta = yaml.safe_load(f) or {}
    else:
        meta = {}

    # Ensure the ``data`` section exists
    meta.setdefault("data", {})
    meta["data"]["processed_timestamp"] = timestamp
    meta["data"]["processed_version"] = version
    meta["data"]["processed_path"] = str(output_path)

    # Write back
    with meta_path.open("w", encoding="utf-8") as f:
        yaml.dump(meta, f, default_flow_style=False)

def main():
    """
    Stand‑alone entry point (not used by the quickstart but kept for
    completeness). It simply validates that the processed CSV exists and
    updates the metadata file.
    """
    cfg_path = Path("data/metadata.yaml")
    processed_path = Path("data/processed/filtered_galaxies.csv")

    if not processed_path.is_file():
        raise FileNotFoundError(f"{processed_path} not found")

    timestamp = datetime.utcnow().isoformat()
    update_metadata(
        metadata_path=str(cfg_path),
        output_path=str(processed_path),
        timestamp=timestamp,
    )
    print(f"Metadata updated at {cfg_path}")

    return 0

if __name__ == "__main__":
    exit(main())
