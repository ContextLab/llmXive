"""
ingest.py
----------

End‑to‑end ingestion orchestrator.

This script coordinates the validation and featurization steps for the
diffusion dataset. It:

1. Ensures the raw dataset is present (real or synthetic).
2. Validates each CSV row using ``ingestion.validate.validate_row``.
   Invalid rows are logged with the appropriate tags.
3. Featurizes all *valid* rows via ``ingestion.featurize.featurize_row``.
   Rows that cannot be featurized (e.g. missing solvent descriptors) are
   skipped and a warning is logged.
4. Writes the featurized records to
   ``data/processed/featurized_data.jsonl``.
5. Writes the number of **featurized** records to
   ``data/processed/valid_record_count.txt`` (this count now matches the
   actual number of JSON‑L entries).
6. Updates the data‑source flag (real vs synthetic) by invoking
   ``ingestion.flag_source.main``.
"""

import csv
import json
import sys
from pathlib import Path
from typing import List

from utils.logging import get_logger, log_error, log_info
from ingestion.validate import validate_row
from ingestion.featurize import featurize_row
from ingestion.flag_source import main as update_data_source_flag
from utils.config import get_project_root

logger = get_logger()

def _load_raw_rows(raw_path: Path) -> List[dict]:
    """Read the raw CSV and return a list of row dictionaries."""
    with raw_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def _write_featurized_jsonl(records: List[dict], output_path: Path) -> None:
    """Write each record as a JSON line."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")

def _write_valid_count(count: int, count_path: Path) -> None:
    """Write the integer count of *featurized* records."""
    count_path.parent.mkdir(parents=True, exist_ok=True)
    count_path.write_text(str(count), encoding="utf-8")

def ingest(root: Path) -> bool:
    """
    Run the full ingestion pipeline.

    Returns
    -------
    bool
        ``True`` on success, ``False`` on any fatal error.
    """
    raw_dir = root / "data" / "raw"
    processed_dir = root / "data" / "processed"

    raw_path = raw_dir / "dataset.csv"
    if not raw_path.is_file():
        log_error(logger, f"Raw dataset not found at {raw_path}")
        return False

    # Load rows from the raw CSV
    rows = _load_raw_rows(raw_path)

    valid_rows: List[dict] = []
    featurized_records: List[dict] = []

    for row in rows:
        if validate_row(row):
            valid_rows.append(row)
            try:
                feat = featurize_row(row)
                if feat is not None:
                    featurized_records.append(feat)
                else:
                    # This should be rare; log for traceability.
                    log_error(
                        logger,
                        f"Featurization returned None for SMILES "
                        f"'{row.get('smiles', row.get('SMILES', 'unknown'))}'",
                    )
            except Exception as exc:
                log_error(
                    logger,
                    f"Featurization failed for SMILES "
                    f"'{row.get('smiles', row.get('SMILES', 'unknown'))}': {exc}",
                )
        # ``validate_row`` already logs tags for invalid rows.

    # Write JSON‑L output
    jsonl_path = processed_dir / "featurized_data.jsonl"
    _write_featurized_jsonl(featurized_records, jsonl_path)

    # Write count of featurized records (matches JSON‑L length)
    count_path = processed_dir / "valid_record_count.txt"
    _write_valid_count(len(featurized_records), count_path)

    log_info(
        logger,
        f"Ingestion finished: {len(featurized_records)} valid rows written to {jsonl_path}",
    )

    # Update the data‑source flag (real vs synthetic)
    try:
        update_data_source_flag()
    except Exception as exc:
        log_error(logger, f"Failed to update data source flag: {exc}")
        # Not fatal for ingestion itself
    return True

def main() -> None:
    """CLI entry point."""
    root = get_project_root()
    success = ingest(root)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
