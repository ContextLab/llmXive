"""
code/data/fetch_heas.py
-----------------------

This module downloads a curated High‑Entropy Alloy (HEA) yield‑strength
dataset from Zenodo, validates each record against the JSON‑schema contract
`contracts/dataset.schema.yaml`, and writes the cleaned CSV to
``data/raw/heas_raw.csv``.

The implementation follows the contract‑driven approach used throughout
the project:

* The dataset URL is obtained from the configuration (`utils.config.get_config()`).
  If the configuration does not provide a URL, the module falls back to a
  Zenodo search for the first public record matching the keywords
  “high entropy alloy yield strength” that contains a suitable CSV file.
* Each row is validated with ``jsonschema.validate``; a missing required
  field (e.g. ``yield_strength``) raises a ``ValueError`` with a clear
  message, satisfying the FR‑009 abort‑on‑missing‑field requirement.
* The function returns the ``Path`` to the written CSV for downstream
  callers.
"""

import csv
import json
import re
import io
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List

import requests
import yaml
from jsonschema import validate, ValidationError

from utils.config import get_config
from utils.logging import get_logger

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_schema() -> Dict[str, Any]:
    """
    Load the dataset JSON‑schema from ``contracts/dataset.schema.yaml``.
    """
    schema_path = Path(__file__).resolve().parents[2] / "contracts" / "dataset.schema.yaml"
    if not schema_path.is_file():
        raise FileNotFoundError(f"Dataset schema not found at {schema_path}")
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _validate_row(row: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Validate a single row (dictionary) against the loaded schema.
    Raises ``ValueError`` with a helpful message if validation fails.
    """
    try:
        validate(instance=row, schema=schema)
    except ValidationError as exc:
        # Provide a concise error that points to the offending field.
        field = exc.path[0] if exc.path else "unknown"
        raise ValueError(
            f"Row validation error (field '{field}'): {exc.message}"
        ) from exc

def _download_file(url: str, dest_path: Path) -> None:
    """
    Download a file from ``url`` and write it to ``dest_path``.
    """
    logger.info(f"Downloading file from {url}")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_bytes(resp.content)

def _extract_csv_from_zip(zip_path: Path) -> Path:
    """
    Extract the first CSV file found inside ``zip_path`` to a temporary
    location and return the Path to the extracted CSV.
    """
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.namelist():
            if member.lower().endswith(".csv"):
                with zf.open(member) as src, tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                    shutil.copyfileobj(src, tmp)
                    return Path(tmp.name)
    raise RuntimeError(f"No CSV file found inside ZIP archive {zip_path}")

def _download_from_zenodo(search_query: str = "high entropy alloy yield strength") -> Path:
    """
    Perform a Zenodo API search for the given query, pick the first public
    record that contains a CSV file (or a ZIP containing a CSV), and download
    that file. Returns the temporary ``Path`` to the downloaded CSV.
    """
    logger.info(f"Searching Zenodo for dataset matching query: '{search_query}'")
    api_url = "https://zenodo.org/api/records"
    # Request a larger result set to improve the chance of finding a suitable CSV.
    params = {"q": search_query, "size": 20, "sort": "mostviewed"}
    response = requests.get(api_url, params=params, timeout=30)
    response.raise_for_status()
    records = response.json().get("hits", {}).get("hits", [])

    if not records:
        raise RuntimeError(f"No Zenodo records found for query '{search_query}'")

    for rec in records:
        files = rec.get("files", [])
        for f in files:
            filename = f.get("key", "")
            lower_name = filename.lower()
            # Prefer CSV files whose name indicates they contain yield‑strength data.
            if lower_name.endswith(".csv") and "yield" in lower_name:
                download_url = f["links"]["download"]
                logger.info(f"Downloading CSV '{filename}' from {download_url}")
                tmp_path = Path.cwd() / "data" / "raw" / filename
                _download_file(download_url, tmp_path)
                return tmp_path
            # If a ZIP archive is found, attempt to extract a CSV from it.
            if lower_name.endswith(".zip"):
                download_url = f["links"]["download"]
                logger.info(f"Downloading ZIP '{filename}' from {download_url}")
                zip_tmp = Path.cwd() / "data" / "raw" / filename
                _download_file(download_url, zip_tmp)
                csv_path = _extract_csv_from_zip(zip_tmp)
                # Clean up the zip file after extraction.
                zip_tmp.unlink(missing_ok=True)
                return csv_path

    raise RuntimeError("No suitable CSV (or ZIP containing CSV) found in Zenodo search results")

def _parse_composition(comp_str: str) -> Dict[str, float]:
    """
    Parse composition strings such as ``Al0.3Co0.3Cr0.3`` or
    ``Al(0.3)Co(0.3)Cr(0.3)`` into a dictionary mapping element symbols to
    their atomic fractions. This helper is retained for compatibility
    with downstream descriptor code that expects a ``composition`` field
    expressed as a JSON string.
    """
    # Normalise the string: remove whitespace, ensure parentheses are optional
    comp_str = comp_str.replace(" ", "")
    # Regex captures element symbols (capital letter + optional lowercase) and a numeric value
    pattern = r"([A-Z][a-z]?)(?:\(?([0-9]*\.?[0-9]+)\)?)"
    matches = re.findall(pattern, comp_str)
    if not matches:
        raise ValueError(f"Unable to parse composition string: '{comp_str}'")
    composition = {}
    for element, fraction in matches:
        composition[element] = float(fraction)
    # Normalise to sum to 1 if they don't already
    total = sum(composition.values())
    if total == 0:
        raise ValueError("Composition fractions sum to zero")
    for k in composition:
        composition[k] /= total
    return composition

# ----------------------------------------------------------------------
# Main public function
# ----------------------------------------------------------------------
def fetch_heas() -> Path:
    """
    Download the HEA dataset, validate every row, and write the cleaned CSV
    to ``data/raw/heas_raw.csv``.

    Returns
    -------
    pathlib.Path
        Path to the written CSV file.

    Raises
    ------
    RuntimeError
        If the dataset cannot be fetched.
    ValueError
        If any row fails schema validation (e.g. missing ``yield_strength``).
    """
    # Determine source URL
    config = get_config()
    dataset_url = config.get("hea_dataset_url")  # user‑provided URL, optional

    if dataset_url:
        logger.info(f"Downloading HEA dataset from configured URL: {dataset_url}")
        response = requests.get(dataset_url, timeout=30)
        response.raise_for_status()
        csv_path = Path.cwd() / "data" / "raw" / "heas_raw_downloaded.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        csv_path.write_bytes(response.content)
    else:
        # Fallback to Zenodo search
        csv_path = _download_from_zenodo()

    # Load CSV into memory (using the csv module to keep dependencies minimal)
    logger.info(f"Reading dataset from {csv_path}")
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows: List[Dict[str, Any]] = list(reader)

    if not rows:
        raise RuntimeError("Downloaded dataset is empty")

    schema = _load_schema()

    # Validate each row; also ensure the ``composition`` field is a JSON string
    # that can be parsed into a dict for downstream steps.
    for idx, row in enumerate(rows, start=1):
        # Convert composition column if present and not already JSON
        if "composition" in row and isinstance(row["composition"], str):
            try:
                comp_dict = json.loads(row["composition"])
            except json.JSONDecodeError:
                # Try to parse free‑form string
                comp_dict = _parse_composition(row["composition"])
            row["composition"] = comp_dict

        try:
            _validate_row(row, schema)
        except ValueError as exc:
            raise ValueError(f"Validation failed for row {idx}: {exc}") from exc

    # Write the validated data to the canonical location
    output_path = Path(__file__).resolve().parents[2] / "data" / "raw" / "heas_raw.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Writing validated dataset to {output_path}")

    # Use csv.DictWriter to preserve original column order
    fieldnames = rows[0].keys()
    with output_path.open("w", newline="", encoding="utf-8") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            # Ensure composition is stored as JSON string for consistency
            if isinstance(row.get("composition"), dict):
                row["composition"] = json.dumps(row["composition"])
            writer.writerow(row)

    logger.info("HEA dataset download and validation completed successfully")
    return output_path

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Command‑line entry point for ``python -m code.data.fetch_heas``.
    """
    try:
        path = fetch_heas()
        print(f"Dataset written to: {path}")
    except Exception as exc:
        logger.exception("Failed to fetch HEA dataset")
        sys.exit(1)

if __name__ == "__main__":
    main()
