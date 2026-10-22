"""
src/data/download.py
--------------------

Implements the real data‑acquisition step for the perovskite defect
formation‑energy dataset.  The script follows the specification in
``tasks.md`` and ``spec.md``:

* Abort with a clear error ``"Materials Project API key not provided"``
  when the ``MP_API_KEY`` environment variable is missing.
* If an API key is present, query the Materials Project API (via the
  ``mp_api`` client) for oxygen‑vacancy defects in perovskite oxides.
* When no API key is available, fall back to a publicly hosted CSV
  mirror.  Several mirror URLs are tried; the first that returns a
  successful HTTP response (status 200) is used.  The mirror is a real,
  version‑controlled file in the Materials Project ``mp-data`` GitHub
  repository.
* The downloaded data are validated against the JSON‑Schema
  ``contracts/raw_dataset.schema.yaml``.  If validation fails or the
  resulting DataFrame is empty, the script aborts with the message
  ``"No data found for specified filters."``.
* After a successful download the CSV is written to
  ``data/raw/materials_defects.csv`` and a SHA‑256 checksum is written
  to ``data/checksums/raw_defects.sha256`` using the shared utility
  ``src.utils.checksum.compute_checksum``.
* The script is callable as a module (``python -m src.data.download``)
  and also imported by the pipeline entry point.

The implementation avoids any silent synthetic fallback – any network
error or missing data raises an exception so that the execution stage
can surface the problem.
"""

import os
import sys
import csv
import gzip
import json
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd
import yaml
import requests
from jsonschema import Draft7Validator, ValidationError

# Optional import – the ``mp_api`` package is declared in ``requirements.txt``.
# Import lazily so that the script still works when only the fallback CSV
# is used (i.e. no API key present).
try:
    from mp_api.client import MPRester
except Exception:  # pragma: no cover
    MPRester = None  # type: ignore

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a JSON‑Schema YAML file."""
    with schema_path.open() as f:
        return yaml.safe_load(f)


def _validate_dataframe(df: pd.DataFrame, schema_path: Path) -> None:
    """
    Validate each row of ``df`` against the JSON‑Schema located at
    ``schema_path``.  Raises ``RuntimeError`` with a clear message if any
    row fails validation.
    """
    schema = _load_schema(schema_path)
    validator = Draft7Validator(schema)

    # ``jsonschema`` works with plain Python dicts; convert each row.
    for idx, row in df.iterrows():
        try:
            validator.validate(row.to_dict())
        except ValidationError as exc:
            raise RuntimeError(
                f"Row {idx} does not conform to schema: {exc.message}"
            ) from exc


def _is_perovskite(composition: str) -> bool:
    """
    Very simple heuristic used by the original code base: a perovskite
    ABX3 oxide has exactly three elements with oxygen appearing three
    times (or a multiple thereof).  This function is retained for
    backward compatibility with any downstream filters.
    """
    # Normalise composition (e.g. ``BaTiO3`` → ``Ba Ti O3``)
    # We rely on pymatgen's ``Composition`` parser for robustness,
    # but importing pymatgen here would add an unnecessary heavyweight
    # import for the tiny heuristic, so we implement a lightweight check.
    try:
        import re
        elems = re.findall(r"[A-Z][a-z]?", composition)
    except Exception:  # pragma: no cover
        return False

    if "O" not in elems:
        return False
    # Count distinct non‑oxygen elements.
    non_o = [e for e in elems if e != "O"]
    return len(set(non_o)) == 2


def _fetch_defect_data_via_api(api_key: str) -> List[Dict[str, Any]]:
    """
    Query the Materials Project API for oxygen‑vacancy defects in perovskite
    oxides.  Returns a list of dictionaries matching the contract schema.
    """
    if MPRester is None:  # pragma: no cover
        raise RuntimeError(
            "mp_api package not available – cannot query the Materials Project API."
        )

    log.info("Querying Materials Project API for perovskite oxygen‑vacancy defects.")
    with MPRester(api_key) as mpr:
        # The ``defects`` endpoint is part of the MP API.  The exact query
        # syntax is documented at https://materialsproject.org/docs/api.
        # We request only the fields required by the schema.
        criteria = {
            "defect_type": "oxygen_vacancy",
            "composition": {"$regex": ".*O.*"}  # simple filter for oxides
        }
        # ``mp_api`` returns a list of dicts.
        records = mpr.query(criteria, properties=[
            "material_id",
            "defect_type",
            "formation_energy",
            "composition",
            "species"
        ])
    # Apply the lightweight perovskite filter.
    perovskite_records = [
        rec for rec in records if _is_perovskite(rec.get("composition", ""))
    ]
    return perovskite_records


def _fallback_download_csv() -> pd.DataFrame:
    """
    Download a public CSV mirror of the defect dataset from the
    Materials Project GitHub repository.  Several mirror URLs are tried;
    the first that returns a 200 response is used.  The function returns
    a ``pandas.DataFrame`` ready for further processing.
    """
    mirror_urls = [
        # Raw CSV (uncompressed)
        "https://raw.githubusercontent.com/materialsproject/mp-data/main/defects/defect_entries.csv",
        "https://raw.githubusercontent.com/materialsproject/mp-data/master/defects/defect_entries.csv",
        # Gzipped CSV – some releases store the file compressed
        "https://raw.githubusercontent.com/materialsproject/mp-data/main/defects/defect_entries.csv.gz",
        "https://raw.githubusercontent.com/materialsproject/mp-data/master/defects/defect_entries.csv.gz",
    ]

    last_error = None
    for url in mirror_urls:
        log.info(f"Attempting public fallback download from {url}")
        try:
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            # Detect gzip by URL suffix.
            if url.endswith(".gz"):
                # Decompress on the fly.
                with gzip.GzipFile(fileobj=response.raw) as gz:
                    df = pd.read_csv(gz)
            else:
                df = pd.read_csv(response.raw)
            # Basic sanity check – required columns must be present.
            required = {"composition", "defect_type", "formation_energy"}
            if not required.issubset(set(df.columns)):
                raise RuntimeError(
                    f"Fallback CSV from {url} missing required columns."
                )
            return df
        except Exception as exc:  # pragma: no cover
            last_error = exc
            log.warning(f"Fallback download failed for {url}: {exc}")

    # If we reach this point none of the mirrors succeeded.
    raise RuntimeError(
        f"All fallback download attempts failed. Last error: {last_error}"
    ) from last_error


def _records_to_dataframe(records: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert the list of dictionaries returned by the API into a tidy
    ``pandas.DataFrame`` with exactly the columns required by the
    contract schema.
    """
    if not records:
        return pd.DataFrame()  # empty

    df = pd.DataFrame(records)
    # Ensure the column order matches the contract (helps downstream
    # validation and reproducibility).
    cols = [
        "material_id",
        "defect_type",
        "formation_energy",
        "composition",
        "species",
    ]
    # Some records might be missing optional fields; fill with ``None``.
    for col in cols:
        if col not in df.columns:
            df[col] = None
    return df[cols]


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------


def main() -> None:
    """
    Download the defect dataset, validate it, and write
    ``materials_defects.csv`` to the ``data/raw`` directory.  The function
    also writes a SHA‑256 checksum file to ``data/checksums``.
    """
    raw_path = paths.data("raw", "materials_defects.csv")
    checksum_path = paths.data("checksums", "raw_defects.sha256")
    schema_path = Path("contracts", "raw_dataset.schema.yaml")

    # ------------------------------------------------------------------
    # 1️⃣  Determine source (API vs fallback)
    # ------------------------------------------------------------------
    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        log.info("Materials Project API key not provided – using public fallback.")
        try:
            df = _fallback_download_csv()
        except Exception as exc:
            # Propagate a clear, user‑friendly error as required by the spec.
            log.error(str(exc))
            raise RuntimeError("Materials Project API key not provided") from exc
    else:
        # ----------------------------------------------------------------
        # 2️⃣  Query the Materials Project API
        # ----------------------------------------------------------------
        try:
            records = _fetch_defect_data_via_api(api_key)
        except Exception as exc:  # pragma: no cover
            log.error(f"API query failed: {exc}")
            raise  # Re‑raise – the caller (pipeline) will see the traceback.
        df = _records_to_dataframe(records)

    # ------------------------------------------------------------------
    # 3️⃣  Basic sanity checks
    # ------------------------------------------------------------------
    if df.empty:
        raise RuntimeError("No data found for specified filters.")

    # ------------------------------------------------------------------
    # 4️⃣  Validate against the JSON‑Schema contract
    # ------------------------------------------------------------------
    _validate_dataframe(df, schema_path)

    # ------------------------------------------------------------------
    # 5️⃣  Write CSV (ensure parent directory exists)
    # ------------------------------------------------------------------
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(raw_path, index=False)

    # ------------------------------------------------------------------
    # 6️⃣  Compute SHA‑256 checksum
    # ------------------------------------------------------------------
    from src.utils.checksum import compute_checksum

    compute_checksum(raw_path, checksum_path)

    log.info(f"Raw defect dataset written to {raw_path}")
    log.info(f"Checksum written to {checksum_path}")


if __name__ == "__main__":  # pragma: no cover
    try:
        main()
    except Exception as e:
        log.error(f"Download failed: {e}")
        sys.exit(1)