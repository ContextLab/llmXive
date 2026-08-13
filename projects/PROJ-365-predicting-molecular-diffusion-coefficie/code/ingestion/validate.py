"""
Ingestion validation utilities.

This module provides functions to validate individual rows of the raw diffusion
dataset. Validation includes:
  * SMILES string validation using RDKit.
  * Detection of missing solvent‑related variables (any column whose name starts
    with ``solvent_``).

Rows that fail validation are excluded from downstream processing and the
corresponding events are logged using the project's logging utilities.

The module can also be executed as a script to filter a CSV file of raw data,
writing only the validated rows to an output CSV file.
"""

import csv
from pathlib import Path
from typing import Dict, Iterable, List

from rdkit import Chem

from utils.logging import (
    get_logger,
    log_invalid_smiles,
    log_missing_data_excluded,
)
from utils.config import get_project_root

__all__ = [
    "is_valid_smiles",
    "validate_row",
    "filter_valid_rows",
    "main",
]


def is_valid_smiles(smiles: str) -> bool:
    """
    Return ``True`` if ``smiles`` can be parsed by RDKit, otherwise ``False``.
    """
    if not isinstance(smiles, str) or not smiles.strip():
        return False
    mol = Chem.MolFromSmiles(smiles)
    return mol is not None


def _solvent_fields(row: Dict[str, str]) -> List[str]:
    """
    Return a list of keys in ``row`` that correspond to solvent descriptors.
    The convention used throughout the project is that any column whose name
    starts with ``solvent_`` (case‑insensitive) stores a solvent variable.
    """
    return [k for k in row.keys() if k.lower().startswith("solvent_")]


def validate_row(row: Dict[str, str]) -> bool:
    """
    Validate a single CSV row.

    The validation criteria are:
      1. The SMILES string must be present and parsable by RDKit.
      2. All solvent descriptor columns must contain a non‑empty value.

    If a row fails a check, an appropriate log entry is emitted and ``False`` is
    returned. Otherwise ``True`` is returned.
    """
    logger = get_logger()

    # ----------------------------------------------------------------------
    # 1. SMILES validation
    # ----------------------------------------------------------------------
    smiles = row.get("smiles") or row.get("SMILES")
    if not smiles:
        logger.debug("Row missing SMILES column.")
        log_invalid_smiles("MISSING_SMILES")
        return False
    if not is_valid_smiles(smiles):
        logger.debug(f"Invalid SMILES detected: {smiles}")
        log_invalid_smiles(smiles)
        return False

    # ----------------------------------------------------------------------
    # 2. Solvent descriptor completeness
    # ----------------------------------------------------------------------
    solvent_keys = _solvent_fields(row)
    missing_keys = [k for k in solvent_keys if not row.get(k)]
    if missing_keys:
        logger.debug(
            f"Row missing solvent data for fields: {', '.join(missing_keys)}"
        )
        log_missing_data_excluded(", ".join(missing_keys))
        return False

    # All checks passed
    return True


def filter_valid_rows(
    rows: Iterable[Dict[str, str]],
) -> List[Dict[str, str]]:
    """
    Filter an iterable of CSV rows, returning only those that pass
    :func:`validate_row`.
    """
    return [row for row in rows if validate_row(row)]


def main() -> None:
    """
    Command‑line entry point.

    Reads the raw dataset CSV (default ``data/raw/dataset.csv``), filters out
    invalid rows, and writes the validated rows to
    ``data/processed/validated.csv``. Paths can be overridden via the
    ``--input`` and ``--output`` arguments.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate raw diffusion dataset CSV."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=get_project_root() / "data" / "raw" / "dataset.csv",
        help="Path to the raw CSV file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=get_project_root() / "data" / "processed" / "validated.csv",
        help="Path where the validated CSV will be written.",
    )
    args = parser.parse_args()

    input_path: Path = args.input
    output_path: Path = args.output

    logger = get_logger()
    logger.info(f"Starting validation: {input_path}")

    if not input_path.is_file():
        logger.error(f"Input file does not exist: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open(newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        rows = list(reader)

    valid_rows = filter_valid_rows(rows)

    if not valid_rows:
        logger.warning("No valid rows found after validation.")
    else:
        logger.info(f"{len(valid_rows)} / {len(rows)} rows passed validation.")

    # Write out the validated rows preserving the original header order
    with output_path.open("w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
        writer.writeheader()
        writer.writerows(valid_rows)

    logger.info(f"Validated CSV written to: {output_path}")

if __name__ == "__main__":
    main()