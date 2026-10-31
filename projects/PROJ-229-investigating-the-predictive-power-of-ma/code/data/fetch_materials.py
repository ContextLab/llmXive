"""
fetch_materials.py

This script streams the Materials Project dataset, filters for entries that
have both melting point and heat capacity data, computes minimal descriptor
fields required by `contracts/dataset.schema.yaml` and writes the result
as a Parquet file.

The implementation uses only the standard `logging` module (to avoid
circular-import issues with the project's custom logger) and falls back
to the public `matbench` HuggingFace dataset if the Materials Project API
is unavailable or the API key is missing.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List

import pandas as pd
from pymatgen.core import Composition

from config import get_api_key

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
MIN_ROWS = 5_000  # minimum number of records required after filtering
OUTPUT_PATH = Path("data/raw/pcm.parquet")

# Set up a simple module-level logger
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
def _fetch_from_mp_api(api_key: str) -> Iterable[Dict[str, Any]]:
    """
    Query the Materials Project REST API for a broad set of materials
    including the required thermodynamic properties.
    Returns a generator to avoid loading the entire dataset into memory.
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
        # Use the context manager to ensure the client is closed
        with MaterialsProjectRestClient(api_key) as client:
            logger.info("Requesting materials from Materials Project ...")
            # client.query returns a generator
            yield from client.query(
                criteria={},  # no filter – get everything
                properties=properties,
            )
    except Exception as exc:
        logger.error(f"Materials Project query failed: {exc}")
        raise

def _fallback_matbench() -> Iterable[Dict[str, Any]]:
    """
    Load a verified matbench dataset as a fallback source.
    Returns an iterator over the records.
    """
    try:
        from datasets import load_dataset
    except Exception as exc:
        logger.error(f"`datasets` package not available: {exc}")
        raise

    try:
        # The matbench collection includes a thermal-properties subset.
        ds = load_dataset(
            "matbench",
            "matbench_expt_thermal_properties",
            split="train",
        )
        logger.info(f"Loaded records from matbench fallback.")
        yield from ds
    except Exception as exc:
        logger.error(f"Failed to load matbench fallback dataset: {exc}")
        raise

def _filter_and_enrich(records: Iterable[Dict[str, Any]]) -> pd.DataFrame:
    """
    Keep only records that have both melting point and heat capacity,
    compute `elemental_count` from the formula and reshape the data to
    match `contracts/dataset.schema.yaml`.
    """
    filtered: List[Dict[str, Any]] = []
    
    for idx, rec in enumerate(records):
        # Filter for entries that have both melting point and heat capacity
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

        # Construct the record to exactly match contracts/dataset.schema.yaml
        enriched = {
            "material_id": str(material_id),
            "composition": str(formula),
            "elemental_count": int(elemental_count),
            "formation_energy": float(rec.get("formation_energy_per_atom", 0.0)),
            "density": float(rec.get("density", float("nan"))),
            # Placeholder empty feature vectors; later steps will fill them.
            "elemental_features": [],
            "graph_features": [],
        }
        filtered.append(enriched)

    if not filtered:
        raise RuntimeError(
            "No records with both melting point and heat capacity were found."
        )

    return pd.DataFrame(filtered)

def _validate_row_count(df: pd.DataFrame) -> None:
    """
    Ensure the filtered dataset meets the minimum row-count requirement.
    """
    row_count = len(df)
    if row_count < MIN_ROWS:
        raise RuntimeError(
            f"Insufficient filtered records: {row_count} < required {MIN_ROWS}"
        )
    logger.info(
        f"Validated filtered dataset size: {row_count} rows (>= {MIN_ROWS})."
    )

def _write_parquet(df: pd.DataFrame) -> None:
    """
    Write the DataFrame to Parquet using `pyarrow`.
    """
    try:
        import pyarrow
    except ImportError as exc:
        logger.error("PyArrow is required for Parquet output but is not installed.")
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
    """
    # Step 1: obtain API key; if missing, trigger fallback immediately.
    try:
        api_key = get_api_key()
    except Exception as exc:
        logger.warning(
            f"Could not obtain Materials Project API key ({exc}); using fallback dataset."
        )
        api_key = None

    # Step 2 & 3: fetch data (using generators to stay within memory limits)
    if api_key:
        try:
            raw_records_gen = _fetch_from_mp_api(api_key)
            logger.info("Successfully initialized fetch from Materials Project.")
        except Exception:
            logger.warning("Primary MP fetch failed; attempting matbench fallback.")
            raw_records_gen = _fallback_matbench()
    else:
        raw_records_gen = _fallback_matbench()

    # Step 4: filter and enrich (consumes the generator)
    df = _filter_and_enrich(raw_records_gen)

    # Step 5: validate row count
    _validate_row_count(df)

    # Step 6: write Parquet file
    _write_parquet(df)

if __name__ == "__main__":
    main()
