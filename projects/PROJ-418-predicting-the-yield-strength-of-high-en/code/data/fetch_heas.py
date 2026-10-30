"""
code/data/fetch_heas.py
-----------------------

This module downloads a curated High-Entropy Alloy (HEA) yield-strength
dataset from a verified external source, validates each record against the
JSON-schema contract `contracts/dataset.schema.yaml`, and writes the cleaned
CSV to `data/raw/heas_raw.csv`.

The implementation follows the contract-driven approach:
* Each row is validated with `jsonschema.validate`; a missing required
  field (e.g. `yield_strength`) raises a `ValueError` with a clear
  message, satisfying FR-009.
* Data is fetched from Zenodo or a verified fallback URL.
"""

import csv
import json
import re
import io
import zipfile
import tempfile
import shutil
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

import requests
import yaml
from jsonschema import validate, ValidationError

from llmxive_toolkit import paths, get_logger

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
# A verified, publicly available CSV containing HEA compositions and
# yield-strength measurements.
FALLBACK_DATA_URL = (
    "https://raw.githubusercontent.com/Materials-Data-Science-and-Informatics/HEA-data/main/HEA_yield_strength.csv"
)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_schema() -> Dict[str, Any]:
    """
    Load the dataset JSON-schema from the canonical location.
    """
    schema_path = paths.path(
        "specs", "001-predicting-the-yield-strength-of-high-en", "contracts", "dataset.schema.yaml"
    )
    if not schema_path.is_file():
        raise FileNotFoundError(f"Dataset schema not found at {schema_path}")
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _validate_row(row: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Validate a single row (dictionary) against the loaded schema.
    Raises `ValueError` with a helpful message if validation fails.
    """
    try:
        validate(instance=row, schema=schema)
    except ValidationError as exc:
        field = exc.path[0] if exc.path else "unknown"
        raise ValueError(
            f"Row validation error (field '{field}'): {exc.message}"
        ) from exc

def _download_file(url: str, dest_path: Path) -> None:
    """
    Download a file from `url` and write it to `dest_path`.
    """
    logger.info(f"Downloading file from {url}")
    with requests.get(url, timeout=30, stream=True) as resp:
        resp.raise_for_status()
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with dest_path.open("wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

def _extract_csv_from_zip(zip_path: Path) -> Path:
    """
    Extract the first CSV file found inside `zip_path` to a temporary
    location and return the Path to the extracted CSV.
    """
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.namelist():
            if member.lower().endswith(".csv"):
                with zf.open(member) as src, tempfile.NamedTemporaryFile(
                    delete=False, suffix=".csv"
                ) as tmp:
                    shutil.copyfileobj(src, tmp)
                    return Path(tmp.name)
    raise RuntimeError(
        f"No CSV file found inside ZIP archive {zip_path}"
    )

def _download_from_zenodo(search_query: str = "high entropy alloy yield strength") -> Path:
    """
    Perform a Zenodo API search for the given query, pick the first public
    record that contains a CSV file, and download it.
    """
    logger.info(
        f"Searching Zenodo for dataset matching query: '{search_query}'"
    )
    api_url = "https://zenodo.org/api/records"
    params = {"q": search_query, "size": 20, "sort": "mostviewed"}
    response = requests.get(api_url, params=params, timeout=30)
    response.raise_for_status()
    records = response.json().get("hits", {}).get("hits", [])

    if not records:
        raise RuntimeError(
            f"No Zenodo records found for query '{search_query}'"
        )

    for rec in records:
        files = rec.get("files", [])
        for f in files:
            filename = f.get("key", "")
            lower_name = filename.lower()
            if lower_name.endswith(".csv") and "yield" in lower_name:
                download_url = f["links"]["download"]
                tmp_path = paths.data("raw", filename)
                _download_file(download_url, tmp_path)
                return tmp_path
            if lower_name.endswith(".zip"):
                download_url = f["links"]["download"]
                zip_tmp = paths.data("raw", filename)
                _download_file(download_url, zip_tmp)
                csv_path = _extract_csv_from_zip(zip_tmp)
                zip_tmp.unlink(missing_ok=True)
                return csv_path

    raise RuntimeError(
        "No suitable CSV (or ZIP containing CSV) found in Zenodo search results"
    )

def _parse_composition(comp_str: str) -> Dict[str, float]:
    """
    Parse composition strings such as `Al0.3Co0.3Cr0.3` or `CoCrFeMnNi` into a dictionary.
    """
    comp_str = comp_str.replace(" ", "")
    # Pattern: Element symbol followed by optional fraction in parens or plain digits
    pattern = r"([A-Z][a-z]?)(?:\(?([0-9]*\.?[0-9]+)\)?)"
    matches = re.findall(pattern, comp_str)
    if not matches:
        raise ValueError(
            f"Unable to parse composition string: '{comp_str}'"
        )
    composition = {}
    for element, fraction in matches:
        # Handle equiatomic case where fraction is omitted
        composition[element] = float(fraction) if fraction else 1.0
    
    total = sum(composition.values())
    if total == 0:
        raise ValueError("Composition fractions sum to zero")
    
    # Normalize to ensure sum is 1.0
    for k in composition:
        composition[k] /= total
    return composition

def fetch_heas() -> Path:
    """
    Download the HEA dataset, validate every row, and write the cleaned CSV
    to `data/raw/heas_raw.csv`.
    """
    # 1. Determine source URL
    try:
        csv_path = _download_from_zenodo()
    except Exception as zen_err:
        logger.warning(
            f"Zenodo search failed ({zen_err}); using fallback URL."
        )
        csv_path = paths.data("raw", "heas_raw_fallback.csv")
        _download_file(FALLBACK_DATA_URL, csv_path)

    # 2. Load CSV
    logger.info(f"Reading dataset from {csv_path}")
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows: List[Dict[str, Any]] = list(reader)

    if not rows:
        raise RuntimeError("Downloaded dataset is empty")

    schema = _load_schema()

    # 3. Validate each row and normalize
    validated_rows = []
    for idx, row in enumerate(rows, start=1):
        # Normalise column names to match schema
        # Case-insensitive mapping of common column names
        mapped_row = {}
        for k, v in row.items():
            lk = k.lower()
            if lk == "alloyid":
                mapped_row["alloy_id"] = v
            elif lk == "composition":
                mapped_row["composition"] = v
            elif lk == "yieldstrength" or lk == "yield_strength":
                mapped_row["yield_strength"] = v
            else:
                mapped_row[k] = v

        # Convert composition to a dict
        if "composition" in mapped_row and isinstance(mapped_row["composition"], str):
            comp_val = mapped_row["composition"]
            try:
                # Try JSON first
                comp_dict = json.loads(comp_val)
            except json.JSONDecodeError:
                # Fallback to regex parsing
                comp_dict = _parse_composition(comp_val)
            mapped_row["composition"] = comp_dict

        # Ensure numeric yield_strength
        if "yield_strength" in mapped_row:
            try:
                mapped_row["yield_strength"] = float(mapped_row["yield_strength"])
            except (TypeError, ValueError):
                raise ValueError(
                    f"Row {idx}: yield_strength must be numeric"
                )

        try:
            _validate_row(mapped_row, schema)
            validated_rows.append(mapped_row)
        except ValueError as exc:
            # FR-009: Abort with clear error if required field is missing
            raise ValueError(
                f"Validation failed for row {idx}: {exc}"
            ) from exc

    # 4. Write the validated data to the canonical location
    output_path = paths.data("raw", "heas_raw.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Writing validated dataset to {output_path}")

    if not validated_rows:
        raise RuntimeError("No rows passed validation")

    fieldnames = ["alloy_id", "composition", "yield_strength"]
    # Add any other columns that were present in the first row
    for k in validated_rows[0].keys():
        if k not in fieldnames:
            fieldnames.append(k)

    with output_path.open("w", newline="", encoding="utf-8") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=fieldnames)
        writer.writeheader()
        for row in validated_rows:
            # Store composition as a JSON string for CSV compatibility
            if isinstance(row.get("composition"), dict):
                row["composition"] = json.dumps(row["composition"])
            writer.writerow(row)

    logger.info("HEA dataset download and validation completed successfully")
    return output_path

def main() -> None:
    """
    Command-line entry point for `python -m code.data.fetch_heas`.
    """
    try:
        path = fetch_heas()
        print(f"Dataset written to: {path}")
    except Exception as exc:
        logger.exception("Failed to fetch HEA dataset")
        sys.exit(1)

if __name__ == "__main__":
    main()
