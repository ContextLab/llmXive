"""
fetch_materials.py

This script streams the Materials Project dataset, filters for entries that
have both melting point and heat capacity data, computes minimal descriptor
fields required by ``contracts/dataset.schema.yaml`` and writes the result
as a Parquet file.

The implementation deliberately avoids importing the top‑level ``utils``
package (which currently has circular‑import issues) and instead imports
the concrete logger functions directly from ``code.utils.logger``.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from pymatgen.core import Composition

from code.utils.logger import (
    get_pipeline_logger,
    log_error,
    log_info,
    log_warning,
)
from config import get_api_key

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
MIN_ROWS = 5_000  # minimum number of records required after filtering
OUTPUT_PATH = Path("data/raw/pcm.parquet")

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _fetch_from_mp_api(api_key: str) -> List[Dict[str, Any]]:
    """
    Query the Materials Project REST API for a broad set of materials
    including the required thermodynamic properties.

    Parameters
    ----------
    api_key : str
        The Materials Project API key.

    Returns
    -------
    List[Dict[str, Any]]
        A list of material dictionaries returned by the API.
    """
    try:
        from mp_api.client import MaterialsProjectRestClient
    except Exception as exc:
        log_error(f"Unable to import mp_api client: {exc}")
        raise

    # The API allows us to request a large number of entries without a
    # specific filter.  We ask for the fields we need for this task.
    properties = [
        "material_id",
        "pretty_formula",
        "melting_point",
        "heat_capacity",
        "formation_energy_per_atom",
        "density",
    ]

    try:
        with MaterialsProjectRestClient(api_key) as client:
            # ``query`` returns a generator; we collect all results.
            log_info("Requesting materials from Materials Project ...")
            records = list(
                client.query(
                    criteria={},  # no filter – get everything
                    properties=properties,
                )
            )
            log_info(f"Retrieved {len(records)} raw records from MP.")
            return records
    except Exception as exc:
        log_error(f"Materials Project query failed: {exc}")
        raise

def _fallback_matbench() -> List[Dict[str, Any]]:
    """
    Load a verified matbench dataset as a fallback source.  The selected
    subset contains the required thermodynamic fields.
    """
    try:
        from datasets import load_dataset
    except Exception as exc:
        log_error(f"datasets package not available: {exc}")
        raise

    try:
        # The matbench dataset "matbench_expt_thermal_properties" includes
        # melting point and heat capacity for a large number of compounds.
        ds = load_dataset(
            "matbench",
            "matbench_expt_thermal_properties",
            split="train",
        )
        records = [dict(row) for row in ds]
        log_info(f"Loaded {len(records)} records from matbench fallback.")
        return records
    except Exception as exc:
        log_error(f"Failed to load matbench fallback dataset: {exc}")
        raise

def _filter_and_enrich(records: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Keep only records that have both melting point and heat capacity,
    compute ``elemental_count`` from the formula and reshape the data to
    match ``contracts/dataset.schema.yaml``.
    """
    filtered: List[Dict[str, Any]] = []
    for rec in records:
        mp = rec.get("melting_point")
        hc = rec.get("heat_capacity")
        if mp is None or hc is None:
            continue

        formula = rec.get("pretty_formula")
        if not formula:
            continue

        try:
            comp = Composition(formula)
            elemental_count = len(comp.elements)
        except Exception:
            # If the formula cannot be parsed we skip the entry.
            continue

        enriched = {
            "material_id": rec.get("material_id"),
            "composition": formula,
            "elemental_count": elemental_count,
            # The schema expects a numeric formation energy; we use the
            # per‑atom value if present, otherwise 0.0.
            "formation_energy": rec.get("formation_energy_per_atom", 0.0),
            # Density may be missing – use NaN which the schema accepts as a
            # number (float).  Pandas will store it as ``float``.
            "density": rec.get("density", float("nan")),
            # The schema defines ``elemental_features`` and ``graph_features``
            # as arrays of numbers.  At this stage we have not computed them,
            # so we store empty lists (they will be filled later in the
            # pipeline).
            "elemental_features": [],
            "graph_features": [],
        }
        filtered.append(enriched)

    if not filtered:
        raise RuntimeError("No records with both melting point and heat capacity were found.")

    df = pd.DataFrame(filtered)
    return df

def _validate_row_count(df: pd.DataFrame) -> None:
    """
    Ensure the filtered dataset meets the minimum row‑count requirement.
    """
    row_count = len(df)
    if row_count < MIN_ROWS:
        raise RuntimeError(
            f"Insufficient filtered records: {row_count} < required {MIN_ROWS}"
        )
    log_info(f"Validated filtered dataset size: {row_count} rows (≥ {MIN_ROWS}).")

# ----------------------------------------------------------------------
# Main routine
# ----------------------------------------------------------------------
def main() -> None:
    """
    Entry point for the script.

    The function:
    1. Reads the Materials Project API key from the configuration.
    2. Attempts to fetch the full dataset from MP.
    3. Falls back to a public matbench dataset on any exception.
    4. Filters for entries that contain both melting point and heat capacity.
    5. Validates the row count.
    6. Writes the resulting DataFrame to ``data/raw/pcm.parquet``.
    """
    logger = get_pipeline_logger(__name__)

    api_key = get_api_key()
    try:
        raw_records = _fetch_from_mp_api(api_key)
        log_info("Successfully fetched data from Materials Project.")
    except Exception as exc:
        log_warning(f"Primary MP fetch failed ({exc}); using matbench fallback.")
        try:
            raw_records = _fallback_matbench()
            log_info("Successfully loaded fallback matbench dataset.")
        except Exception as fallback_exc:
            log_error(f"Both primary and fallback data sources failed: {fallback_exc}")
            raise

    # Filter, enrich and reshape
    df = _filter_and_enrich(raw_records)

    # Validate minimum size
    _validate_row_count(df)

    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Write Parquet file
    try:
        df.to_parquet(OUTPUT_PATH, index=False)
        log_info(f"Filtered PCM dataset written to {OUTPUT_PATH}")
    except Exception as exc:
        log_error(f"Failed to write Parquet file: {exc}")
        raise

if __name__ == "__main__":
    main()
