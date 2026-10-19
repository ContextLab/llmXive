"""
code/data/fetch_heas.py
-----------------------

Fetches the curated High‑Entropy Alloy (HEA) yield‑strength dataset from a
Zenodo repository, validates each record against the JSON‑schema contract,
and writes the validated data to ``data/raw/heas_raw.csv``.

The URL of the Zenodo dataset must be provided via the environment variable
``ZENODO_URL``.  This design allows the test suite to point the script at a
temporary HTTP server serving a minimal CSV fixture while still satisfying the
requirement that a *real* URL is used in production.

The script aborts loudly (raises an exception) if:
  * The environment variable is missing.
  * The HTTP request fails (non‑200 status).
  * The CSV cannot be parsed.
  * Any row does not conform to ``contracts/dataset.schema.yaml``.
  * Required fields are missing (fulfils FR‑009).

The implementation relies only on the standard library, ``requests`` and
``jsonschema`` (both available in the runner) and uses the project‑wide
``paths`` helper to place the output file in the correct location.
"""

import csv
import json
import os
from pathlib import Path
from typing import Dict, Any

import requests
from jsonschema import validate, ValidationError

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
OUTPUT_CSV_PATH = paths.data("raw", "heas_raw.csv")
SCHEMA_PATH = Path(__file__).resolve().parents[2] / "contracts" / "dataset.schema.yaml"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_schema() -> Dict[str, Any]:
    """Load the JSON‑schema used to validate each dataset row."""
    if not SCHEMA_PATH.is_file():
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_PATH}")
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

def _parse_composition(comp_str: str) -> Dict[str, float]:
    """
    The ``composition`` column in the CSV is expected to be a JSON‑encoded
    object mapping element symbols to their atomic fractions (e.g. ``{
    "Fe": 0.2, "Cr": 0.2, "Ni": 0.6}``).  This helper parses the string
    safely, raising ``ValueError`` if the JSON is malformed.
    """
    try:
        comp = json.loads(comp_str)
        if not isinstance(comp, dict):
            raise ValueError("Composition must be a JSON object.")
        # Ensure all fractions are numbers between 0 and 1
        for elem, frac in comp.items():
            if not isinstance(elem, str):
                raise ValueError(f"Element symbol must be a string, got {type(elem)}")
            if not isinstance(frac, (int, float)):
                raise ValueError(f"Fraction for element {elem} must be numeric.")
            if not (0.0 <= frac <= 1.0):
                raise ValueError(f"Fraction for element {elem} out of bounds: {frac}")
        return comp
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in composition column: {exc}") from exc

def _validate_row(row: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Validate a single row against the dataset schema.  The ``composition``
    field is converted from its JSON string representation to a dict before
    validation because the schema expects an object.
    """
    # Convert composition string to dict for validation
    if "composition" in row:
        row["composition"] = _parse_composition(row["composition"])
    try:
        validate(instance=row, schema=schema)
    except ValidationError as exc:
        raise ValueError(f"Row validation error: {exc.message}") from exc

# ----------------------------------------------------------------------
# Main function
# ----------------------------------------------------------------------
def fetch_heas() -> Path:
    """
    Download the HEA dataset, validate it, and write the clean CSV to disk.

    Returns
    -------
    pathlib.Path
        Path to the written CSV file.
    """
    # ------------------------------------------------------------------
    # 1️⃣ Resolve the Zenodo URL
    # ------------------------------------------------------------------
    zenodo_url = os.getenv("ZENODO_URL")
    if not zenodo_url:
        raise RuntimeError(
            "Environment variable 'ZENODO_URL' not set. "
            "Provide the full URL to the Zenodo CSV file before running the script."
        )
    log.info(f"Downloading HEA dataset from {zenodo_url}")

    # ------------------------------------------------------------------
    # 2️⃣ Stream the download (fails loudly on HTTP errors)
    # ------------------------------------------------------------------
    response = requests.get(zenodo_url, stream=True, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to download dataset: HTTP {response.status_code} from {zenodo_url}"
        )
    response.raise_for_status()

    # ------------------------------------------------------------------
    # 3️⃣ Parse CSV and validate rows
    # ------------------------------------------------------------------
    schema = _load_schema()
    rows = []
    csv_reader = csv.DictReader(
        (line.decode("utf-8") for line in response.iter_lines(decode_unicode=False)),
        skipinitialspace=True,
    )
    for line_no, raw_row in enumerate(csv_reader, start=2):  # header is line 1
        # Ensure required columns are present
        required_cols = {"alloy_id", "composition", "yield_strength", "phase", "temperature"}
        missing = required_cols - raw_row.keys()
        if missing:
            raise ValueError(
                f"Missing required columns {missing} in CSV line {line_no}"
            )

        # Normalise field types where appropriate
        row = {
            "alloy_id": raw_row["alloy_id"].strip(),
            "composition": raw_row["composition"].strip(),
            "yield_strength": float(raw_row["yield_strength"]),
            "phase": raw_row["phase"].strip(),
            "temperature": float(raw_row["temperature"]),
        }

        # Validate against JSON‑schema (will also catch missing fields)
        _validate_row(row, schema)
        rows.append(row)

    if not rows:
        raise RuntimeError("Downloaded dataset is empty after validation.")

    # ------------------------------------------------------------------
    # 4️⃣ Write validated CSV to the canonical location
    # ------------------------------------------------------------------
    OUTPUT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["alloy_id", "composition", "yield_strength", "phase", "temperature"],
        )
        writer.writeheader()
        for row in rows:
            # ``composition`` must be written back as JSON text
            row_to_write = row.copy()
            row_to_write["composition"] = json.dumps(row_to_write["composition"], separators=(",", ":"))
            writer.writerow(row_to_write)

    log.info(f"HEA dataset written to {OUTPUT_CSV_PATH} ({len(rows)} records).")
    return OUTPUT_CSV_PATH

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    CLI wrapper so the script can be invoked with ``python -m code.data.fetch_heas``.
    Any exception propagates to the caller, causing a non‑zero exit status
    (required for the verification tests).
    """
    try:
        fetch_heas()
    except Exception as exc:
        log.error(f"Failed to fetch HEA dataset: {exc}")
        raise

if __name__ == "__main__":
    main()