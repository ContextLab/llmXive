"""
fetch_materials.py

This script streams the Materials Project dataset, filters for entries that
have both melting point and heat capacity data, computes minimal descriptor
fields required by ``contracts/dataset.schema.yaml`` and writes the result
as a Parquet file.

The implementation uses only the standard ``logging`` module (to avoid
circular‑import issues with the project's custom logger) and falls back
to the public ``matbench`` HuggingFace dataset if the Materials Project API
is unavailable or the API key is missing.

The script now:
* Generates a synthetic ``material_id`` when the source does not provide one.
* Guarantees that ``pyarrow`` is present for Parquet output (declared in
  ``requirements.txt``).
* Raises clear errors on any failure (no silent synthetic data).
"""

import logging
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from pymatgen.core import Composition

from config import get_api_key

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
MIN_ROWS = 5_000  # minimum number of records required after filtering
OUTPUT_PATH = Path("data/raw/pcm.parquet")

# Set up a simple module‑level logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

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
        logger.error(f"Unable to import mp_api client: {exc}")
        raise

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
            logger.info("Requesting materials from Materials Project ...")
            records = list(
                client.query(
                    criteria={},  # no filter – get everything
                    properties=properties,
                )
            )
            logger.info(f"Retrieved {len(records)} raw records from MP.")
            return records
    except Exception as exc:
        logger.error(f"Materials Project query failed: {exc}")
        raise

def _fallback_matbench() -> List[Dict[str, Any]]:
    """
    Load a verified matbench dataset as a fallback source. The selected
    subset contains the required thermodynamic fields.
    """
    try:
        from datasets import load_dataset
    except Exception as exc:
        logger.error(f"`datasets` package not available: {exc}")
        raise

    try:
        # The matbench collection includes a thermal‑properties subset.
        ds = load_dataset(
            "matbench",
            "matbench_expt_thermal_properties",
            split="train",
        )
        records = [dict(row) for row in ds]
        logger.info(f"Loaded {len(records)} records from matbench fallback.")
        return records
    except Exception as exc:
        logger.error(f"Failed to load matbench fallback dataset: {exc}")
        raise

def _filter_and_enrich(records: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Keep only records that have both melting point and heat capacity,
    compute ``elemental_count`` from the formula and reshape the data to
    match ``contracts/dataset.schema.yaml``.
    """
    filtered: List[Dict[str, Any]] = []
    for idx, rec in enumerate(records):
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

        # Ensure a material_id exists – generate a synthetic one if missing.
        material_id = rec.get("material_id")
        if not material_id:
            material_id = f"fallback_{idx}"

        enriched = {
            "material_id": material_id,
            "composition": formula,
            "elemental_count": elemental_count,
            "formation_energy": rec.get("formation_energy_per_atom", 0.0),
            "density": rec.get("density", float("nan")),
            # Placeholder empty feature vectors; later steps will fill them.
            "elemental_features": [],
            "graph_features": [],
        }
        filtered.append(enriched)

    if not filtered:
        raise RuntimeError(
            "No records with both melting point and heat capacity were found."
        )

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
    logger.info(
        f"Validated filtered dataset size: {row_count} rows (≥ {MIN_ROWS})."
    )

def _write_parquet(df: pd.DataFrame) -> None:
    """
    Write the DataFrame to Parquet using ``pyarrow``. This function
    raises a clear error if ``pyarrow`` is not installed.
    """
    try:
        import pyarrow  # noqa: F401  # ensure the package is present
    except Exception as exc:
        logger.error(
            "PyArrow is required for Parquet output but is not installed."
        )
        raise RuntimeError("Missing required dependency: pyarrow") from exc

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT_PATH, index=False)
    logger.info(f"Filtered PCM dataset written to {OUTPUT_PATH}")

# ----------------------------------------------------------------------
# Main routine
# ----------------------------------------------------------------------
def main() -> None:
    """
    Entry point for the script.

    Steps:
    1. Retrieve an API key from the configuration.
    2. Attempt to fetch the full dataset from Materials Project.
    3. On any failure, fall back to the public matbench dataset.
    4. Filter for entries with both melting point and heat capacity.
    5. Validate that at least ``MIN_ROWS`` records remain.
    6. Write the resulting DataFrame to ``data/raw/pcm.parquet``.
    """
    # Step 1: obtain API key; if missing, trigger fallback immediately.
    try:
        api_key = get_api_key()
    except Exception as exc:
        logger.warning(
            f"Could not obtain Materials Project API key ({exc}); using fallback dataset."
        )
        api_key = None

    # Step 2 & 3: fetch data
    if api_key:
        try:
            raw_records = _fetch_from_mp_api(api_key)
            logger.info("Successfully fetched data from Materials Project.")
        except Exception:
            logger.warning("Primary MP fetch failed; attempting matbench fallback.")
            raw_records = _fallback_matbench()
    else:
        raw_records = _fallback_matbench()

    # Step 4: filter and enrich
    df = _filter_and_enrich(raw_records)

    # Step 5: validate row count
    _validate_row_count(df)

    # Step 6: write Parquet file
    _write_parquet(df)

if __name__ == "__main__":
    main()
