"""
fetch_materials.py
------------------
Fetch raw Materials Project data using the ``mp-api`` library.
If the Materials Project API cannot be accessed (e.g., missing/invalid API key,
rate‑limit, network error), fall back to the verified ``matbench`` dataset.
The script validates that the fallback dataset contains a column that can be used
as a Materials Project identifier (``material_id`` or an equivalent field).  If
such a column is missing, a ``FileNotFoundError`` is raised with a clear
explanatory message.

The resulting raw data is saved as JSON to ``data/raw/materials_project_data.json``.
The script is intended to be executed directly::

    python code/data/fetch_materials.py

It uses the project's logging utilities and configuration helpers.
"""

import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any

# Project imports (public API surface)
from utils.logger import get_pipeline_logger, log_error, log_warning, log_info
from config import get_api_key

# Optional third‑party imports – they are part of the declared dependencies.
try:
    from mp_api.client import MPRester
except Exception as exc:  # pragma: no cover
    # Import error will be handled later when we attempt to use the library.
    MPRester = None  # type: ignore

from datasets import load_dataset

# -------------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------------
OUTPUT_PATH = Path("data/raw/materials_project_data.json")
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------
def _fetch_via_mp_api() -> List[Dict[str, Any]]:
    """
    Retrieve Materials Project entries using the mp-api client.

    Returns
    -------
    List[Dict[str, Any]]
        A list of dictionaries, each representing a material entry.
    """
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError(
            "Materials Project API key not found. Set it in the environment or "
            "config.yaml before using mp-api."
        )

    if MPRester is None:
        raise ImportError(
            "mp-api package could not be imported. Ensure it is installed."
        )

    logger = get_pipeline_logger(__name__)
    logger.info("Attempting to fetch data from Materials Project via mp-api.")

    # Define the fields we need. The exact field names are taken from the
    # Materials Project schema – ``material_id`` is always present.
    fields = [
        "material_id",
        "pretty_formula",
        "melting_point",
        "heat_of_fusion",  # latent heat of fusion (J/g)
    ]

    with MPRester(api_key) as mpr:
        # The query returns a list of dicts.
        docs = mpr.summary.search(
            criteria={},
            properties=fields,
            # We keep the request lightweight – pagination handled internally.
            # ``max_entries`` is set high enough to retrieve the full dataset;
            # mp-api will stream results as needed.
            max_entries=100_000,
        )
    logger.info(f"Fetched {len(docs)} records from Materials Project.")
    return docs

def _fetch_matbench_fallback() -> List[Dict[str, Any]]:
    """
    Load the verified Matbench dataset as a fallback source.

    Returns
    -------
    List[Dict[str, Any]]
        List of material records from the Matbench dataset.
    """
    logger = get_pipeline_logger(__name__)
    logger.info(
        "Falling back to the Matbench dataset (matbench_v0.1) as a substitute."
    )

    # The Matbench dataset family provides a ``material_id`` column that matches
    # the Materials Project identifiers.
    ds = load_dataset("matbench", "matbench_v0.1", split="train", streaming=False)
    # Convert to a list of dicts (pandas is not a hard requirement here)
    records = [dict(row) for row in ds]

    logger.info(f"Loaded {len(records)} records from Matbench fallback.")
    return records

def _validate_fallback(records: List[Dict[str, Any]]) -> None:
    """
    Ensure the fallback dataset contains a Materials Project identifier.

    Parameters
    ----------
    records : List[Dict[str, Any]]
        The dataset rows to validate.

    Raises
    ------
    FileNotFoundError
        If no appropriate identifier column is present.
    """
    if not records:
        raise FileNotFoundError(
            "Matbench fallback dataset is empty – cannot proceed."
        )

    # Look for a column that can serve as a Material Project ID.
    candidate_keys = {"material_id", "mpid", "mp_id", "task_id"}
    present_keys = set(records[0].keys())
    if not candidate_keys.intersection(present_keys):
        raise FileNotFoundError(
            "Matbench fallback dataset does not contain a Materials Project ID "
            "column (expected one of: material_id, mpid, mp_id, task_id)."
        )

def _write_json(data: List[Dict[str, Any]]) -> None:
    """
    Write the list of dictionaries to the designated JSON file.

    Parameters
    ----------
    data : List[Dict[str, Any]]
        The data to serialize.
    """
    with OUTPUT_PATH.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)
    log_info(f"Saved raw materials data to {OUTPUT_PATH}")

# -------------------------------------------------------------------------
# Main orchestration
# -------------------------------------------------------------------------
def main() -> None:
    """
    Entry point for the script.

    Attempts to fetch data from the Materials Project API; on failure,
    falls back to the Matbench dataset, validates the presence of a
    Materials Project identifier, and writes the result to JSON.
    """
    logger = get_pipeline_logger(__name__)
    try:
        records = _fetch_via_mp_api()
    except Exception as exc:  # pragma: no cover
        # Log the exception details for debugging, then attempt fallback.
        log_warning(
            f"Materials Project fetch failed ({type(exc).__name__}): {exc}"
        )
        logger.debug("Exception details:", exc_info=True)
        try:
            records = _fetch_matbench_fallback()
            _validate_fallback(records)
        except Exception as fallback_exc:
            # Propagate a clear error – the pipeline cannot continue without
            # a compatible dataset.
            log_error(
                f"Fallback to Matbench also failed ({type(fallback_exc).__name__}): "
                f"{fallback_exc}"
            )
            raise FileNotFoundError(
                "Both Materials Project and Matbench data sources are unavailable "
                "or incompatible. Cannot continue."
            ) from fallback_exc

    # At this point ``records`` holds a list of dicts ready for downstream steps.
    _write_json(records)

if __name__ == "__main__":
    # When run as a script we configure the logger first.
    # ``setup_logger`` is part of the utils.logger public API.
    from utils.logger import setup_logger

    # Initialise a simple console logger; the project config may override this.
    setup_logger()
    main()
