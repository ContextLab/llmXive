"""
Descriptor computation utilities.

The public API already includes functions for computing various molecular
descriptors. The ``main`` entry point now loads the raw SMILES file,
computes the full descriptor set and writes the result to
``data/processed/descriptors.csv``.
"""

import logging
from typing import List

import pandas as pd
from rdkit import Chem

from llmxive_toolkit import paths, get_logger

from code.descriptors import (
    compute_all_descriptors,
)  # re‑import to keep the original implementation

log = get_logger(__name__)

def main() -> int:
    """Compute descriptors for the raw SMILES dataset."""
    raw_path = paths.data("raw", "smiles.csv")
    out_path = paths.data("processed", "descriptors.csv")

    log.info(f"Reading SMILES from {raw_path}")
    df = pd.read_csv(raw_path)
    if "smiles" not in df.columns:
        log.error("Input file missing 'smiles' column.")
        return 1

    # Compute descriptors – the function expects a DataFrame with a 'smiles' column
    log.info("Computing descriptors...")
    descriptors_df = compute_all_descriptors(df)

    # Write output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    descriptors_df.to_csv(out_path, index=False)
    log.info(f"Wrote descriptors to {out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
