"""
code/data/fetch_heas.py
-----------------------

Fetches the curated High‑Entropy Alloy (HEA) yield‑strength dataset from a
Zenodo repository (or an alternative URL provided via configuration), validates
each record against the JSON‑schema contract, and writes the validated data to
``data/raw/heas_raw.csv``.

The script aborts loudly (raises an exception) if:
  * No URL is provided via the ``ZENODO_URL`` environment variable nor the
    project configuration.
  * The HTTP request fails (non‑200 status) when a remote URL is used.
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
from utils.config import get_config

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
    object mapping element symbols to their atomic fractions (e.g.
    ``{\"Fe\": 0.2, \"Cr\": 0.2, \"Ni\": 0.6}``).  This helper parses the string
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

def _resolve_zenodo_url() -> str:
    """
    Resolve the dataset URL using the following precedence:
    1. ``ZENODO_URL`` environment variable.
    2. ``zenodo_url`` (or ``dataset_url``) entry in the project config
       obtained via ``utils.config.get_config``.
    If neither is available, a ``RuntimeError`` is raised.
    """
    # 1️⃣ Environment variable
    zenodo_url = os.getenv("ZENODO_URL")
    if zenodo_url:
        return zenodo_url

    # 2️⃣ Configuration file fallback
    try:
        cfg = get_config()
    except Exception as exc:
        raise RuntimeError(
            "Unable to load project configuration to obtain the dataset URL."
        ) from exc

    # Accept either key name – be permissive
    for key in ("zenodo_url", "dataset_url", "data_url"):
        if key in cfg and cfg[key]:
            return cfg[key]

    raise RuntimeError(
        "Dataset URL not provided. Set the 'ZENODO_URL' environment variable "
        "or supply a 'zenodo_url' entry in the project configuration."
    )

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
    # 1️⃣ Resolve the Zenodo (or configured) URL
    # ------------------------------------------------------------------
    zenodo_url = _resolve_zenodo_url()
    log.info(f"Downloading HEA dataset from {zenodo_url}")

    # ------------------------------------------------------------------
    # 2️⃣ Retrieve the CSV content
    # ------------------------------------------------------------------
    # Support both HTTP(S) URLs and local file paths.
    if zenodo_url.startswith(("http://", "https://")):
        response = requests.get(zenodo_url, stream=True, timeout=30)
        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to download dataset: HTTP {response.status_code} from {zenodo_url}"
            )
        response.raise_for_status()
        line_iterator = (
            line.decode("utf-8") for line in response.iter_lines(decode_unicode=False)
        )
    else:
        # Assume a local filesystem path (absolute or relative)
        local_path = Path(zenodo_url).expanduser().resolve()
        if not local_path.is_file():
            raise RuntimeError(f"Local dataset file not found at {local_path}")
        line_iterator = (l.rstrip("\n") for l in local_path.open("r", encoding="utf-8"))

    # ------------------------------------------------------------------
    # 3️⃣ Parse CSV and validate rows
    # ------------------------------------------------------------------
    schema = _load_schema()
    rows = []
    csv_reader = csv.DictReader(line_iterator, skipinitialspace=True)
    for line_no, raw_row in enumerate(csv_reader, start=2):  # header is line 1
        # Ensure required columns are present
        required_cols = {"alloy_id", "composition", "yield_strength", "phase", "temperature"}
        missing = required_cols - raw_row.keys()
        if missing:
            raise ValueError(
                f"Missing required columns {missing} in CSV line {line_no}"
            )

        # Normalise field types where appropriate
        try:
            row = {
                "alloy_id": raw_row["alloy_id"].strip(),
                "composition": raw_row["composition"].strip(),
                "yield_strength": float(raw_row["yield_strength"]),
                "phase": raw_row["phase"].strip(),
                "temperature": float(raw_row["temperature"]),
            }
        except Exception as exc:
            raise ValueError(
                f"Type conversion error on line {line_no}: {exc}"
            ) from exc

        # Validate against JSON‑schema (also checks for missing fields)
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
            fieldnames=[
                "alloy_id",
                "composition",
                "yield_strength",
                "phase",
                "temperature",
            ],
        )
        writer.writeheader()
        for row in rows:
            # ``composition`` must be written back as a compact JSON string
            row_to_write = row.copy()
            row_to_write["composition"] = json.dumps(
                row_to_write["composition"], separators=(",", ":")
            )
            writer.writerow(row_to_write)

    log.info(
        f"HEA dataset written to {OUTPUT_CSV_PATH} ({len(rows)} records)."
    )
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
