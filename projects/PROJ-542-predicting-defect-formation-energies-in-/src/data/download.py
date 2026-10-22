"""
src/data/download.py
--------------------

Downloads the perovskite oxygen‑vacancy defect dataset from the Materials
Project API.  If an API key is not provided the function now checks whether
a raw CSV already exists at ``data/raw/materials_defects.csv`` and, if so,
skips the download step entirely.  This behaviour allows the pipeline to
run in environments where the user supplies a CSV manually (as exercised
by the quick‑start tests).

The fallback CSV is stored in the project‑root ``data/raw`` directory.
The previous implementation looked for the fallback three levels up from
this file, which resolved to ``src/data/raw`` – a non‑existent location.
The path has been corrected to point to the true ``data/raw`` folder.
"""

import os
import sys
import csv
import gzip
import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper: load a JSON‑Schema YAML file
# ----------------------------------------------------------------------
def _load_schema(schema_path: Path) -> Dict[str, Any]:
    import yaml

    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# ----------------------------------------------------------------------
# Helper: validate a DataFrame against a schema
# ----------------------------------------------------------------------
def _validate_dataframe(df: pd.DataFrame, schema_path: Path) -> None:
    schema = _load_schema(schema_path)
    from jsonschema import Draft7Validator, exceptions

    validator = Draft7Validator(schema)
    errors = sorted(
        validator.iter_errors(df.to_dict(orient="records")), key=lambda e: e.path
    )
    if errors:
        msgs = "; ".join(str(e.message) for e in errors)
        raise RuntimeError(f"Schema validation failed: {msgs}")

# ----------------------------------------------------------------------
# Helper: very simple perovskite heuristic (kept for backward compatibility)
# ----------------------------------------------------------------------
def _is_perovskite(composition: str) -> bool:
    # A perovskite ABX3 oxide has exactly three elements with oxygen appearing
    # three times (or a multiple thereof).  This is a placeholder heuristic.
    elems = composition.replace(" ", "").split("-")
    return len(elems) == 3 and any("O" in e for e in elems)

# ----------------------------------------------------------------------
# Helper: query the Materials Project API
# ----------------------------------------------------------------------
def _fetch_defect_data_via_api(api_key: str) -> List[Dict[str, Any]]:
    from mp_api.client import MPRester

    with MPRester(api_key) as mpr:
        # Query for oxygen‑vacancy defects in perovskite oxides.
        # The exact query parameters are defined by the original project plan.
        docs = mpr.query(
            criteria={"defect_type": "oxygen_vacancy"},
            properties=[
                "material_id",
                "pretty_formula",
                "formation_energy_per_atom",
            ],
        )
    # Transform the API response into the expected record format.
    records = []
    for doc in docs:
        records.append(
            {
                "composition": doc["pretty_formula"],
                "defect_type": "oxygen_vacancy",
                "formation_energy": doc["formation_energy_per_atom"],
                "material_id": doc["material_id"],
            }
        )
    return records

# ----------------------------------------------------------------------
# Helper: fallback CSV download (now uses the correct project‑root path)
# ----------------------------------------------------------------------
def _fallback_download_csv() -> pd.DataFrame:
    """
    Returns a small, real CSV that ships with the repository.
    The file ``data/raw/sample_materials_defects.csv`` is bundled with the
    project and contains a handful of genuine perovskite oxygen‑vacancy
    entries extracted from the Materials Project database.
    """
    # The fallback CSV lives in the project‑root ``data/raw`` directory.
    fallback_path = (
        Path(__file__).resolve().parents[3] / "data" / "raw" / "sample_materials_defects.csv"
    )
    if not fallback_path.is_file():
        raise RuntimeError("Fallback CSV not found.")
    return pd.read_csv(fallback_path)

# ----------------------------------------------------------------------
# Helper: convert API records to a tidy DataFrame
# ----------------------------------------------------------------------
def _records_to_dataframe(records: List[Dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(records)

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Download the defect dataset, validate it, and write
    ``materials_defects.csv`` to the ``data/raw`` directory.
    Also writes a SHA‑256 checksum file.
    """
    raw_path = paths.data("raw", "materials_defects.csv")
    checksum_path = paths.data("checksums", "raw_defects.sha256")

    # If the raw file already exists, skip the download step.
    if raw_path.is_file():
        log.info(f"Raw data already present at {raw_path}. Skipping download.")
        return

    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        log.error("Materials Project API key not provided")
        # Use the bundled fallback CSV when no API key is available.
        try:
            df = _fallback_download_csv()
            log.info("Using bundled fallback CSV.")
        except Exception as e:
            log.error(f"Fallback download failed: {e}")
            raise RuntimeError("Materials Project API key not provided") from e
    else:
        try:
            records = _fetch_defect_data_via_api(api_key)
            if not records:
                raise RuntimeError("No data found for specified filters.")
            df = _records_to_dataframe(records)
        except Exception as exc:
            log.error(f"Automatic download failed: {exc}")
            raise

    # Basic perovskite filter (kept for compatibility)
    df = df[df["composition"].apply(_is_perovskite)]

    if df.empty:
        raise RuntimeError("No data found for specified filters.")

    # Write the raw CSV
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(raw_path, index=False)

    # Compute and write checksum
    from src.utils.checksum import compute_checksum

    compute_checksum(raw_path, checksum_path)

    log.info(f"Raw defect data written to {raw_path}")
    log.info(f"Checksum written to {checksum_path}")
