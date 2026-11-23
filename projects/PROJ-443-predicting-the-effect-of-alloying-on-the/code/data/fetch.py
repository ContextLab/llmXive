"""
Data fetching module for High‑Entropy Alloy (HEA) datasets.

This module retrieves composition and elastic‑constant data from the
Materials Project API (mp‑api) and the Open Quantum Materials Database
(OQMD).  It filters for alloys that contain at least five principal
elements and writes the raw JSON responses to ``data/raw/``.  For each
raw dump a provenance record is generated (SHA‑256 checksum, query
parameters, timestamps, API version) and stored in
``data/source_metadata.yaml`` according to ``contracts/metadata.schema.yaml``.
"""

import os
import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from mp_api.client import MPRester  # mp‑api library
import requests

from .metadata import write_metadata_entry, check_and_update_provenance

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _sha256_of_file(file_path: Path) -> str:
    """Return the SHA‑256 checksum of ``file_path``."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# ----------------------------------------------------------------------
# Materials Project fetcher
# ----------------------------------------------------------------------
def _fetch_from_materials_project(output_path: Path) -> List[Dict[str, Any]]:
    """
    Query the Materials Project for HEA entries that have elastic‑constant
    data and at least five constituent elements.

    The function writes the raw JSON payload to ``output_path`` and
    returns the loaded list of dictionaries.

    Raises
    ------
    RuntimeError
        If the ``MP_API_KEY`` environment variable is not set.
    ConnectionError
        If the request to the MP server fails after the retry limit.
    """
    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Materials Project API key not found. Set the MP_API_KEY environment variable."
        )

    # ``nelements`` is the number of distinct elements in the composition.
    criteria = {"nelements": {"$gte": 5}, "elastic_moduli": {"$exists": True}}
    fields = [
        "material_id",
        "pretty_formula",
        "composition",
        "elastic_moduli",
    ]

    logger.info("Fetching HEA data from Materials Project (criteria=%s)", criteria)

    # Retry logic – up to 3 attempts
    for attempt in range(1, 4):
        try:
            with MPRester(api_key) as mpr:
                docs = mpr.summary.search(
                    criteria=criteria,
                    fields=fields,
                    # ``max_results`` is set high to retrieve the full set;
                    # the API will paginate internally.
                    max_results=10000,
                )
            break
        except Exception as exc:
            logger.warning(
                "Attempt %d/3 to fetch from Materials Project failed: %s",
                attempt,
                exc,
            )
            if attempt == 3:
                raise ConnectionError(
                    "Failed to retrieve data from Materials Project after 3 attempts."
                ) from exc

    # Convert pymatgen Document objects to plain dicts
    raw_data = [doc.as_dict() for doc in docs]

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write raw JSON
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(raw_data, f, indent=2)

    logger.info(
        "Materials Project fetch complete – %d records written to %s",
        len(raw_data),
        output_path,
    )
    return raw_data


# ----------------------------------------------------------------------
# OQMD fetcher
# ----------------------------------------------------------------------
def _fetch_from_oqmd(output_path: Path) -> List[Dict[str, Any]]:
    """
    Retrieve HEA data from OQMD via its public REST endpoint.

    The OQMD API does not require an authentication key for the basic
    query used here.  The endpoint ``https://oqmd.org/api/v1/materials/``
    accepts a JSON payload with ``criteria`` and ``fields`` similar to the
    Materials Project.

    Returns the list of dictionaries and writes the raw JSON to
    ``output_path``.
    """
    base_url = "https://oqmd.org/api/v1/materials/"

    # OQMD uses the same Mongo‑style query language
    criteria = {"nelements": {"$gte": 5}, "elastic_moduli": {"$exists": True}}
    fields = [
        "material_id",
        "pretty_formula",
        "composition",
        "elastic_moduli",
    ]

    payload = {"criteria": criteria, "fields": fields, "max_results": 10000}
    headers = {"Content-Type": "application/json"}

    logger.info("Fetching HEA data from OQMD (criteria=%s)", criteria)

    for attempt in range(1, 4):
        try:
            response = requests.post(
                base_url, json=payload, headers=headers, timeout=30
            )
            response.raise_for_status()
            raw_data = response.json()
            break
        except Exception as exc:
            logger.warning(
                "Attempt %d/3 to fetch from OQMD failed: %s", attempt, exc
            )
            if attempt == 3:
                raise ConnectionError(
                    "Failed to retrieve data from OQMD after 3 attempts."
                ) from exc

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write raw JSON
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(raw_data, f, indent=2)

    logger.info(
        "OQMD fetch complete – %d records written to %s",
        len(raw_data),
        output_path,
    )
    return raw_data


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def fetch_all() -> None:
    """
    Execute the full fetch pipeline:

    1. Retrieve data from Materials Project and OQMD.
    2. Write raw JSON dumps to ``data/raw/``.
    3. Generate/refresh ``data/source_metadata.yaml`` with provenance
       information for each source.
    """
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Materials Project
    # ------------------------------------------------------------------
    mp_path = raw_dir / "materials_project_hea.json"
    mp_data = _fetch_from_materials_project(mp_path)

    mp_checksum = _sha256_of_file(mp_path)
    mp_metadata = {
        "source_name": "Materials Project",
        "api_version": getattr(MPRester, "__version__", "unknown"),
        "query_parameters": {
            "criteria": {"nelements": {"$gte": 5}, "elastic_moduli": {"$exists": True}},
            "fields": [
                "material_id",
                "pretty_formula",
                "composition",
                "elastic_moduli",
            ],
        },
        "timestamp": datetime.utcnow().isoformat(),
        "checksum": mp_checksum,
        "file_path": str(mp_path),
    }
    write_metadata_entry(mp_metadata)

    # ------------------------------------------------------------------
    # OQMD
    # ------------------------------------------------------------------
    oqmd_path = raw_dir / "oqmd_hea.json"
    oqmd_data = _fetch_from_oqmd(oqmd_path)

    oqmd_checksum = _sha256_of_file(oqmd_path)
    oqmd_metadata = {
        "source_name": "OQMD",
        "api_version": "2023‑10‑01",  # OQMD does not expose a version via API
        "query_parameters": {
            "criteria": {"nelements": {"$gte": 5}, "elastic_moduli": {"$exists": True}},
            "fields": [
                "material_id",
                "pretty_formula",
                "composition",
                "elastic_moduli",
            ],
        },
        "timestamp": datetime.utcnow().isoformat(),
        "checksum": oqmd_checksum,
        "file_path": str(oqmd_path),
    }
    write_metadata_entry(oqmd_metadata)

    logger.info("All fetch operations completed successfully.")


# ----------------------------------------------------------------------
# Convenience entry point for ``python -m code.data.fetch``
# ----------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fetch_all()
