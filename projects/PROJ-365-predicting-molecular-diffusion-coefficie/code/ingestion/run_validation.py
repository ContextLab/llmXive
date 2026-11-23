"""
run_validation.py
-----------------
Executes the SMILES and solvent validation logic defined in
``code/ingestion/validate.py`` on the dataset that has been fetched or
generated earlier in the pipeline.

The script:

1. Reads the ``data_source_flag.json`` artifact created by
   ``code/ingestion/flag_source.py`` to log whether the underlying data is
   real or synthetic (this satisfies the dependency on T007c).
2. Loads the raw CSV located at ``data/raw/dataset.csv``.
3. Applies the validation helpers (``filter_valid_rows``) to drop rows with
   invalid SMILES strings or missing solvent information.
4. Writes the filtered records to ``data/processed/validated.csv``.
5. Logs a concise summary of the operation.

The script is intended to be invoked directly from the command line:

    python code/ingestion/run_validation.py

or imported and called via ``run_validation()`` from other pipeline stages.
"""

import csv
import json
from pathlib import Path
from typing import List, Dict

from utils.config import get_project_root
from utils.logging import get_logger, log_info, log_error
from ingestion.validate import filter_valid_rows


def _load_data_source_flag(project_root: Path) -> Dict[str, str]:
    """
    Load the ``data_source_flag.json`` file that records whether the
    dataset is ``real`` or ``synthetic``.

    Parameters
    ----------
    project_root: Path
        The root directory of the project.

    Returns
    -------
    dict
        The parsed JSON content.

    Raises
    ------
    FileNotFoundError
        If the flag file does not exist.
    json.JSONDecodeError
        If the file cannot be parsed.
    """
    flag_path = project_root / "data" / "data_source_flag.json"
    if not flag_path.is_file():
        raise FileNotFoundError(
            f"Data source flag not found at expected location: {flag_path}"
        )
    with flag_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _read_raw_dataset(raw_path: Path) -> List[Dict[str, str]]:
    """
    Read the raw CSV dataset into a list of dictionaries.

    Parameters
    ----------
    raw_path: Path
        Path to ``data/raw/dataset.csv``.

    Returns
    -------
    List[Dict[str, str]]
        Each dict corresponds to a CSV row (header → value).

    Raises
    ------
    FileNotFoundError
        If the CSV does not exist.
    """
    if not raw_path.is_file():
        raise FileNotFoundError(f"Raw dataset not found at {raw_path}")

    with raw_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    return rows


def _write_validated_dataset(
    rows: List[Dict[str, str]], output_path: Path, fieldnames: List[str]
) -> None:
    """
    Write the validated rows to ``validated.csv`` preserving the original
    column order.

    Parameters
    ----------
    rows: List[Dict[str, str]]
        The rows that passed validation.
    output_path: Path
        Destination file (``data/processed/validated.csv``).
    fieldnames: List[str]
        Column order for the CSV writer.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_validation() -> None:
    """
    Main entry point for the validation step.

    It ties together flag loading, raw‑data reading, validation, and
    output generation while emitting structured log messages.
    """
    logger = get_logger()
    project_root = get_project_root()

    # ------------------------------------------------------------------
    # 1. Resolve data source flag (dependency on T007c)
    # ------------------------------------------------------------------
    try:
        flag = _load_data_source_flag(project_root)
        source = flag.get("source", "unknown")
        log_info(logger, f"Data source flag indicates: {source}")
    except Exception as exc:
        log_error(logger, f"Failed to read data source flag: {exc}")
        raise

    # ------------------------------------------------------------------
    # 2. Load raw dataset
    # ------------------------------------------------------------------
    raw_csv_path = project_root / "data" / "raw" / "dataset.csv"
    try:
        raw_rows = _read_raw_dataset(raw_csv_path)
    except Exception as exc:
        log_error(logger, f"Unable to read raw dataset: {exc}")
        raise

    total_rows = len(raw_rows)
    if total_rows == 0:
        log_info(logger, "Raw dataset is empty – nothing to validate.")
        return

    # ------------------------------------------------------------------
    # 3. Apply validation logic
    # ------------------------------------------------------------------
    valid_rows = filter_valid_rows(raw_rows)

    # Preserve original column order; fall back to the header from the raw file.
    fieldnames = list(raw_rows[0].keys()) if raw_rows else []

    # ------------------------------------------------------------------
    # 4. Write validated output
    # ------------------------------------------------------------------
    validated_path = project_root / "data" / "processed" / "validated.csv"
    _write_validated_dataset(valid_rows, validated_path, fieldnames)

    # ------------------------------------------------------------------
    # 5. Log summary
    # ------------------------------------------------------------------
    kept = len(valid_rows)
    log_info(
        logger,
        f"Validation complete: {kept}/{total_rows} rows retained. "
        f"Validated file written to {validated_path}",
    )


def main() -> None:
    """
    CLI entry point – mirrors the typical ``if __name__ == '__main__'`` pattern.
    """
    run_validation()


if __name__ == "__main__":
    main()