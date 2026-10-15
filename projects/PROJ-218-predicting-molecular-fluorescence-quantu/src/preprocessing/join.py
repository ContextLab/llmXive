"""
Join SMILES and Fluorescence Quantum Yield (FQY) datasets on InChIKey.

This script:
  * Loads a Parquet file with SMILES strings.
  * Loads a JSON file with experimental FQY values and optional metadata.
  * Generates InChIKey identifiers for each molecule using RDKit.
  * Performs an inner join on the InChIKey.
  * Requires at least 200 matched records; otherwise aborts with an error.
  * Constructs a ``metadata`` column containing solvent, temperature,
    and measurement_method information (if available).
  * Writes the joined table to ``data/processed/joined.csv``.
  * Logs the number of matches.

The script is intended to be executed via:
    python -m src.preprocessing.join [options]

All paths are resolved through ``llmxive_toolkit.paths`` which ensures
the target directories exist.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd
from rdkit import Chem
from rdkit.Chem import inchi

from llmxive_toolkit import paths, get_logger

# Initialise logger
log: logging.Logger = get_logger(__name__)

def _smiles_to_inchikey(smiles: str) -> str | None:
    """Convert a SMILES string to an InChIKey.

    Returns ``None`` if the SMILES cannot be parsed.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        return inchi.MolToInchiKey(mol)
    except Exception as e:
        log.debug(f"Failed to convert SMILES '{smiles}': {e}")
        return None

def _load_smiles(parquet_path: Path) -> pd.DataFrame:
    """Load SMILES dataset from a Parquet file."""
    log.info(f"Loading SMILES data from {parquet_path}")
    df = pd.read_parquet(parquet_path)
    if 'smiles' not in df.columns:
        raise ValueError("SMILES file must contain a column named 'smiles'")
    df['inchi_key'] = df['smiles'].apply(_smiles_to_inchikey)
    before = len(df)
    df = df.dropna(subset=['inchi_key'])
    after = len(df)
    log.info(f"Dropped {before - after} SMILES that could not be parsed")
    return df

def _load_fqy(json_path: Path) -> pd.DataFrame:
    """Load FQY dataset from a JSON file.

    The JSON is expected to be either a list of records or an object
    containing a list under a ``data`` key.
    """
    log.info(f"Loading FQY data from {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        content = json.load(f)

    # Normalise to a list of dicts
    if isinstance(content, dict):
        # Try common container keys
        if "data" in content and isinstance(content["data"], list):
            records = content["data"]
        else:
            # Assume the dict itself is a single record
            records = [content]
    elif isinstance(content, list):
        records = content
    else:
        raise ValueError("Unexpected JSON structure for FQY data")

    df = pd.DataFrame(records)
    if 'smiles' not in df.columns:
        raise ValueError("FQY JSON must contain a 'smiles' field for each record")
    df['inchi_key'] = df['smiles'].apply(_smiles_to_inchikey)
    before = len(df)
    df = df.dropna(subset=['inchi_key'])
    after = len(df)
    log.info(f"Dropped {before - after} FQY entries with unparsable SMILES")
    return df

def _merge_datasets(smiles_df: pd.DataFrame, fqy_df: pd.DataFrame) -> pd.DataFrame:
    """Inner join on ``inchi_key`` and build the ``metadata`` column."""
    log.info("Merging datasets on InChIKey")
    merged = pd.merge(
        smiles_df,
        fqy_df,
        on="inchi_key",
        how="inner",
        suffixes=("_smiles", "_fqy"),
    )
    match_count = len(merged)
    log.info(f"matches: {match_count}")

    if match_count < 200:
        raise RuntimeError(
            f"Insufficient matches ({match_count}); require at least 200."
        )

    # Build metadata dict per row
    def build_metadata(row):
        meta = {}
        for field in ["solvent", "temperature", "measurement_method"]:
            if field in row and pd.notna(row[field]):
                meta[field] = row[field]
        return json.dumps(meta) if meta else None

    merged["metadata"] = merged.apply(build_metadata, axis=1)

    # Ensure required column exists
    if "inchi_key" not in merged.columns:
        raise RuntimeError("Merged dataframe lacks 'inchi_key' column")

    return merged

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Join SMILES and FQY datasets on InChIKey."
    )
    parser.add_argument(
        "--smiles",
        type=Path,
        required=True,
        help="Path to the SMILES Parquet file.",
    )
    parser.add_argument(
        "--fqy",
        type=Path,
        required=True,
        help="Path to the FQY JSON file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Destination CSV file for the joined dataset.",
    )
    args = parser.parse_args(argv)

    # Resolve paths via llmxive_toolkit (ensures directories exist)
    smiles_path = paths.path(args.smiles)
    fqy_path = paths.path(args.fqy)
    output_path = paths.path(args.output)

    smiles_df = _load_smiles(smiles_path)
    fqy_df = _load_fqy(fqy_path)
    joined_df = _merge_datasets(smiles_df, fqy_df)

    log.info(f"Writing joined dataset to {output_path}")
    joined_df.to_csv(output_path, index=False)
    log.info("Join completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
