"""
Download the verified PubChem dataset and write a CSV of SMILES strings.
This script is used by the main pipeline to ensure raw data exists.
"""
import os
import logging
from pathlib import Path

import datasets

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def download_pubchem_smiles(output_path: Path) -> None:
    """
    Download the dataset ``sagawa/pubchem-10m-canonicalized`` and write a CSV
    containing only the ``smiles`` column.

    Parameters
    ----------
    output_path: Path
        Destination CSV file (including parent directories).
    """
    log.info("Downloading PubChem dataset via HuggingFace datasets...")
    ds = datasets.load_dataset(
        "sagawa/pubchem-10m-canonicalized", split="train", streaming=False
    )
    # Ensure we have a reasonable sized sample for the runner.
    # The full dataset is ~9 M rows; we will write the first 500 000 rows
    # which comfortably fits within the memory/time limits.
    max_rows = 500_000
    smiles = []
    for i, rec in enumerate(ds):
        if i >= max_rows:
            break
        smiles.append(rec["smiles"])

    log.info(f"Collected {len(smiles)} SMILES strings.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as f:
        f.write("smiles\n")
        f.write("\n".join(smiles))
    log.info(f"Wrote raw SMILES to {output_path}")

def main() -> int:
    raw_path = paths.data("raw", "smiles.csv")
    if raw_path.exists():
        log.info(f"Raw data already present at {raw_path}")
        return 0
    download_pubchem_smiles(raw_path)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
