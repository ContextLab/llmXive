"""
Ingestion script for diffusion dataset.

This module reads a CSV file containing molecule‑solvent records, validates
each SMILES string, featurizes valid rows, and writes the results to a JSONL
file. Invalid SMILES are skipped and logged with the ``[ERROR_SMILES]`` tag
via the project's logging utilities.

The implementation builds on the existing ``featurize_row`` helper (which
creates a ``torch_geometric.data.Data`` object) and the shared logging
helpers defined in ``utils.logging``.
"""

import csv
import json
from pathlib import Path
from typing import Dict, Any

from rdkit import Chem

from utils.logging import (
    get_logger,
    log_invalid_smiles,
    log_missing_data_excluded,
)
from ingestion.featurize import featurize_row

def _is_valid_smiles(smiles: str) -> bool:
    """
    Return ``True`` if ``smiles`` can be parsed by RDKit, otherwise ``False``.
    """
    if not smiles:
        return False
    mol = Chem.MolFromSmiles(smiles)
    return mol is not None

def ingest(input_csv: Path, output_jsonl: Path) -> None:
    """
    Process ``input_csv`` and write featurized records to ``output_jsonl``.

    - Rows with missing critical fields are excluded and logged
      via ``log_missing_data_excluded`` (implemented in T013).
    - Rows with an invalid SMILES string are excluded and logged
      via ``log_invalid_smiles`` (the focus of T014).

    The output format is a JSON Lines file where each line contains a
    dictionary with the original SMILES and a string representation of the
    ``torch_geometric`` ``Data`` object produced by ``featurize_row``.
    """
    logger = get_logger()
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)

    with input_csv.open(newline="", encoding="utf-8") as csv_file, \
         output_jsonl.open("w", encoding="utf-8") as out_file:

        reader = csv.DictReader(csv_file)
        for row_number, row in enumerate(reader, start=1):
            # Basic missing‑data guard (already part of T013)
            if any(value == "" or value is None for value in row.values()):
                log_missing_data_excluded(logger, row)
                continue

            smiles = row.get("smiles")
            if not _is_valid_smiles(smiles):
                # Log the error with the required tag and skip the row
                log_invalid_smiles(logger, smiles if smiles else "")
                continue

            # Featurize the valid row
            try:
                data_obj = featurize_row(row)
            except Exception as exc:  # Defensive: any unexpected featurization error
                logger.error(
                    f"Featurization failed for row {row_number} (SMILES={smiles}): {exc}"
                )
                continue

            # Serialize – we cannot JSON‑encode torch tensors directly, so we store
            # a simple representation that downstream steps can reinterpret.
            record: Dict[str, Any] = {
                "smiles": smiles,
                "data_repr": str(data_obj),
            }
            out_file.write(json.dumps(record) + "\n")

def main() -> None:
    """
    CLI entry point.

    Usage:
        python -m ingestion.ingest [--input INPUT_CSV] [--output OUTPUT_JSONL]

    If arguments are omitted, defaults are:
        input  -> data/raw/dataset.csv
        output -> data/processed/featurized.jsonl
    """
    import argparse

    parser = argparse.ArgumentParser(description="Ingest and featurize diffusion data")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/raw/dataset.csv"),
        help="Path to the raw CSV dataset",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/featurized.jsonl"),
        help="Path where the featurized JSONL will be written",
    )
    args = parser.parse_args()

    ingest(args.input, args.output)

if __name__ == "__main__":
    main()
