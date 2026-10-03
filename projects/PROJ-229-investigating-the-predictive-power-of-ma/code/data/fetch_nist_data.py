"""
fetch_nist_data.py

This module fetches experimental thermodynamic data (melting point and enthalpy of fusion)
from the Materials Project API (via the mp-api client). The fetched records are written
to ``data/raw/nist_data.json`` in JSON Lines format (one JSON object per line) to make
streaming possible for large datasets.

The script can be executed directly:
    python code/data/fetch_nist_data.py

It is also importable; the ``main`` function performs the full workflow.
"""

import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from mp_api.client import MaterialsProjectRestClient
from utils.logger import get_pipeline_logger, log_info, log_error, log_warning
from utils.checksum import compute_sha256

# -------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------

# Output location – must match the deliverable path exactly.
OUTPUT_PATH = Path("data/raw/nist_data.json")
# Minimum number of records expected (as per task specification).
MIN_RECORD_COUNT = 500

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------

def _get_api_key() -> str:
    """
    Retrieve the Materials Project API key from the global ``config.yaml``.
    The ``config`` helper is part of the project root and already provides
    ``get_api_key``. Import lazily to avoid circular imports with ``utils``.
    """
    try:
        from config import get_api_key
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("Failed to import config.get_api_key") from exc

    api_key = get_api_key()
    if not api_key:
        raise RuntimeError(
            "Materials Project API key not found in config.yaml. "
            "Please add a valid key under the 'api_keys' section."
        )
    return api_key

def fetch_nist_data() -> List[Dict[str, Any]]:
    """
    Query the Materials Project REST API for experimental thermodynamic data.
    The query pulls the following fields:
        - material_id
        - pretty_formula
        - melting_point
        - enthalpy_of_fusion

    Returns
    -------
    List[Dict[str, Any]]
        A list of dictionaries, each representing a material with the
        requested properties.
    """
    logger = get_pipeline_logger(__name__)
    api_key = _get_api_key()
    client = MaterialsProjectRestClient(api_key=api_key)

    # The Materials Project stores experimental thermodynamic data under the
    # property name ``thermodynamics``; however, the mp-api client provides a
    # convenient shortcut via the ``thermo`` endpoint.
    # We request a fairly large page size to minimise pagination overhead.
    criteria: Dict[str, Any] = {}
    properties = [
        "material_id",
        "pretty_formula",
        "melting_point",
        "enthalpy_of_fusion",
    ]

    logger.info("Requesting NIST thermodynamic data from Materials Project API")
    try:
        # ``query`` returns a list of dictionaries.
        records = client.query(criteria=criteria, properties=properties, chunk_size=1000)
    except Exception as exc:  # pragma: no cover
        logger.error(f"Failed to query Materials Project API: {exc}")
        raise

    # Filter out entries where both target properties are missing.
    filtered = [
        rec
        for rec in records
        if rec.get("melting_point") is not None or rec.get("enthalpy_of_fusion") is not None
    ]

    logger.info(
        f"Fetched {len(records)} records; {len(filtered)} contain at least one target property."
    )
    return filtered

def save_nist_data(records: List[Dict[str, Any]], path: Path = OUTPUT_PATH) -> None:
    """
    Write the list of records to ``path`` in JSON Lines format.
    Also writes a SHA‑256 checksum file alongside the data file.

    Parameters
    ----------
    records : List[Dict[str, Any]]
        The data to be persisted.
    path : Path, optional
        Destination file path. Defaults to ``OUTPUT_PATH``.
    """
    logger = get_pipeline_logger(__name__)

    # Ensure the parent directory exists.
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON Lines.
    with path.open("w", encoding="utf-8") as fp:
        for rec in records:
            json.dump(rec, fp)
            fp.write("\n")

    logger.info(f"Wrote {len(records)} records to {path}")

    # Compute and write checksum.
    checksum = compute_sha256(path)
    checksum_path = path.with_suffix(".sha256")
    checksum_path.write_text(checksum)
    logger.debug(f"Checksum written to {checksum_path}")

def verify_output(path: Path = OUTPUT_PATH, min_records: int = MIN_RECORD_COUNT) -> None:
    """
    Verify that the output file exists, contains at least ``min_records`` records,
    and that its checksum matches the stored value.

    Raises
    ------
    AssertionError
        If any of the checks fail.
    """
    logger = get_pipeline_logger(__name__)

    if not path.is_file():
        raise AssertionError(f"Expected output file {path} does not exist.")

    # Count records (JSON Lines)
    with path.open("r", encoding="utf-8") as fp:
        count = sum(1 for _ in fp)

    if count < min_records:
        raise AssertionError(
            f"Output file {path} contains only {count} records; "
            f"expected at least {min_records}."
        )
    logger.info(f"Record count verification passed ({count} records).")

    # Verify checksum.
    checksum_path = path.with_suffix(".sha256")
    if not checksum_path.is_file():
        raise AssertionError(f"Checksum file {checksum_path} is missing.")
    expected_checksum = checksum_path.read_text().strip()
    actual_checksum = compute_sha256(path)
    if expected_checksum != actual_checksum:
        raise AssertionError(
            f"Checksum mismatch for {path}: expected {expected_checksum}, got {actual_checksum}"
        )
    logger.info("Checksum verification passed.")

# -------------------------------------------------------------------------
# Main entry point
# -------------------------------------------------------------------------

def main() -> None:
    """
    Orchestrates the fetch‑save‑verify workflow.
    """
    logger = get_pipeline_logger(__name__)
    logger.info("Starting NIST data fetch process")

    records = fetch_nist_data()
    save_nist_data(records)
    verify_output()

    logger.info("NIST data fetch completed successfully")

if __name__ == "__main__":  # pragma: no cover
    main()
