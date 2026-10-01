"""
ingest.py
----------
Implements the data ingestion pipeline for the molecular diffusion project.

The script reads the raw CSV dataset, validates each record, featurizes
valid molecules into PyTorch‑Geometric ``Data`` objects, and writes the
resulting records to a JSONL file.

Two error‑handling concerns are covered:

* **Missing critical fields** – logged with the ``[MISSING_DATA_EXCLUDED]``
  tag (handled by ``log_missing_data_excluded`` from ``utils.logging``).
* **Invalid SMILES strings** – logged with the ``[ERROR_SMILES]`` tag
  (handled by ``log_invalid_smiles`` from ``utils.logging``).

The implementation is deliberately defensive: any exception raised while
processing a single row does **not** abort the whole pipeline; the row is
skipped and the appropriate log entry is emitted.
"""

import csv
import json
from pathlib import Path
from typing import Dict, Any

from rdkit import Chem

# Project utilities
from utils.logging import (
    get_logger,
    log_missing_data_excluded,
    log_invalid_smiles,
    log_info,
    log_error,
)
from utils.config import get_project_root

# Ingestion helpers
from ingestion.validate import is_valid_smiles, validate_row
from ingestion.featurize import featurize_row

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Default locations (relative to project root)
DEFAULT_RAW_CSV = Path("data/raw/dataset.csv")
DEFAULT_OUTPUT_JSONL = Path("data/processed/featurized.jsonl")

# ---------------------------------------------------------------------------
# Core ingestion logic
# ---------------------------------------------------------------------------

def _ensure_parent_dir(file_path: Path) -> None:
    """Make sure the parent directory of *file_path* exists."""
    file_path.parent.mkdir(parents=True, exist_ok=True)

def _row_has_missing_critical_fields(row: Dict[str, Any]) -> bool:
    """
    Determine whether a CSV row is missing any critical field.

    Critical fields for the diffusion dataset are:
    - ``smiles`` – the molecular representation
    - ``solvent`` – solvent identifier / name
    - ``temperature`` – measurement temperature (K or °C)
    - ``diffusion_coeff`` – experimental diffusion coefficient

    The exact column names may differ between data sources; we therefore
    treat any empty string or ``None`` value as missing.
    """
    critical_keys = {"smiles", "solvent", "temperature", "diffusion_coeff"}
    for key in critical_keys:
        if key not in row or row[key] in ("", None):
            return True
    return False

def ingest(
    raw_csv_path: Path = DEFAULT_RAW_CSV,
    output_jsonl_path: Path = DEFAULT_OUTPUT_JSONL,
) -> None:
    """
    Run the ingestion pipeline.

    Parameters
    ----------
    raw_csv_path: Path
        Path to the raw CSV dataset.
    output_jsonl_path: Path
        Destination path for the featurized JSONL file.
    """
    logger = get_logger(__name__)
    logger.info("Starting ingestion pipeline")
    logger.debug(f"Reading raw CSV from {raw_csv_path}")

    # Resolve paths relative to the project root for reproducibility
    project_root = get_project_root()
    raw_csv_path = (project_root / raw_csv_path).resolve()
    output_jsonl_path = (project_root / output_jsonl_path).resolve()

    _ensure_parent_dir(output_jsonl_path)

    processed_count = 0
    skipped_missing = 0
    skipped_invalid_smiles = 0

    try:
        with raw_csv_path.open(newline="", encoding="utf-8") as csv_file, \
             output_jsonl_path.open("w", encoding="utf-8") as out_file:

            reader = csv.DictReader(csv_file)
            for row_number, row in enumerate(reader, start=1):
                # -----------------------------------------------------------------
                # 1️⃣ Missing‑data guard
                # -----------------------------------------------------------------
                if _row_has_missing_critical_fields(row):
                    log_missing_data_excluded(
                        logger,
                        row_number=row_number,
                        reason="critical field missing",
                    )
                    skipped_missing += 1
                    continue

                # -----------------------------------------------------------------
                # 2️⃣ SMILES validation
                # -----------------------------------------------------------------
                smiles = row.get("smiles", "").strip()
                if not is_valid_smiles(smiles):
                    log_invalid_smiles(
                        logger,
                        row_number=row_number,
                        smiles=smiles,
                    )
                    skipped_invalid_smiles += 1
                    continue

                # -----------------------------------------------------------------
                # 3️⃣ Full row validation (additional domain checks)
                # -----------------------------------------------------------------
                # ``validate_row`` returns ``True`` if the row passes all checks.
                # It may raise its own logs; we simply honour the boolean result.
                if not validate_row(row):
                    # ``validate_row`` already logs why a row was rejected, so we
                    # just count it as a missing‑data case for statistics.
                    skipped_missing += 1
                    continue

                # -----------------------------------------------------------------
                # 4️⃣ Featurization
                # -----------------------------------------------------------------
                try:
                    featurized = featurize_row(row)
                except Exception as exc:
                    # Any unexpected error during featurisation should not halt the
                    # pipeline. We log it as an error and move on.
                    log_error(
                        logger,
                        f"Featurization failed for row {row_number}: {exc}",
                    )
                    skipped_missing += 1
                    continue

                # -----------------------------------------------------------------
                # 5️⃣ Write to JSONL
                # -----------------------------------------------------------------
                json_line = json.dumps(featurized, ensure_ascii=False)
                out_file.write(json_line + "\n")
                processed_count += 1

    except FileNotFoundError as fnf_err:
        # Critical failure – cannot proceed without the raw CSV.
        log_error(logger, f"Raw CSV not found: {fnf_err}")
        raise

    # -----------------------------------------------------------------------
    # Summary logging
    # -----------------------------------------------------------------------
    log_info(
        logger,
        f"Ingestion completed: {processed_count} records written, "
        f"{skipped_missing} records skipped (missing data), "
        f"{skipped_invalid_smiles} records skipped (invalid SMILES).",
    )
    logger.info("Ingestion pipeline finished")

# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """
    CLI entry point.

    Allows optional positional arguments to override the default input and
    output locations:

    ``python -m ingestion.ingest [raw_csv] [output_jsonl]``
    """
    import sys

    args = sys.argv[1:]
    raw_path = Path(args[0]) if len(args) >= 1 else DEFAULT_RAW_CSV
    out_path = Path(args[1]) if len(args) >= 2 else DEFAULT_OUTPUT_JSONL

    ingest(raw_csv_path=raw_path, output_jsonl_path=out_path)

if __name__ == "__main__":
    main()
