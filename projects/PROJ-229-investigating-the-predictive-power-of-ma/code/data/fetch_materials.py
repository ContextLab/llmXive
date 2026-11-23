"""
fetch_materials.py

This script streams the Materials Project dataset, filters for entries that
have both melting point and heat capacity data, computes minimal descriptor
fields required by `contracts/dataset.schema.yaml` and writes the result
as a Parquet file.

The implementation uses the modern `mp-api` client (MPRester) and falls back
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
    Query the Materials Project REST API using the modern MPRester.
    Returns a generator to avoid loading the entire dataset into memory.
    """
    try:
        from mp_api.client import MPRester
    except ImportError as exc:
        logger.error(f"Unable to import mp_api client: {exc}")
        raise

    try:
        with MPRester(api_key) as mpr:
            logger.info("Requesting materials from Materials Project via MPRester...")
            # We search for materials that have experimental thermodynamic data.
            # Since we need a large set, we query the experimental endpoint.
            # Note: The experimental API structure can vary; we fetch a broad set.
            results = mpr.experimental.search(
                fields=["material_id", "pretty_formula", "melting_point", "heat_capacity"]
            )
            for res in results:
                # The MPRester returns objects; convert to dict
                yield res.dict()
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
    except ImportError as exc:
        logger.error(f"`datasets` package not available: {exc}")
        raise

    try:
        # The matbench collection includes a thermal-properties subset.
        # We load it and yield records.
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
        # Filter for entries that have both melting point and heat capacity.
        # We check for various common key names in case of API/dataset differences.
        mp = rec.get("melting_point") or rec.get("T_m")
        hc = rec.get("heat_capacity") or rec.get("C_p")
        
        if mp is None or hc is None:
            continue

        formula = rec.get("pretty_formula") or rec.get("formula")
        if not formula:
            continue

        try:
            comp = Composition(formula)
            elemental_count = len(comp.elements)
        except Exception:
            continue

        material_id = rec.get("material_id") or rec.get("mp_id")
        if not material_id:
            material_id = f"fallback_{idx}"

        # The schema requires formation_energy and density.
        # These are often in a separate 'summary' call in MP, but for the
        # raw fetch, we provide available values or defaults (0.0/NaN).
        # Later steps in the pipeline (T006) will compute descriptors.
        enriched = {
            "material_id": str(material_id),
            "composition": str(formula),
            "elemental_count": int(elemental_count),
            "formation_energy": float(rec.get("formation_energy_per_atom", 0.0)),
            "density": float(rec.get("density", float("nan"))),
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
        # In a real research environment, if the intersection is small,
        # we would report this. For the pipeline, we raise as per verification.
        raise RuntimeError(
            f"Insufficient filtered records: {row_count} < required {MIN_ROWS}. "
            "The intersection of experimental melting point and heat capacity "
            "is too sparse in the current source."
        )
    logger.info(
        f"Validated filtered dataset size: {row_count} rows (>= {MIN_ROWS})."
    )

def _write_parquet(df: pd.DataFrame) -> None:
    """
    Write the DataFrame to Parquet using `pyarrow`.
    """
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
    try:
        api_key = get_api_key()
    except Exception as exc:
        logger.warning(
            f"Could not obtain Materials Project API key ({exc}); using fallback dataset."
        )
        api_key = None

    if api_key:
        try:
            raw_records_gen = _fetch_from_mp_api(api_key)
            logger.info("Successfully initialized fetch from Materials Project.")
        except Exception as exc:
            logger.warning(f"Primary MP fetch failed ({exc}); attempting matbench fallback.")
            raw_records_gen = _fallback_matbench()
    else:
        raw_records_gen = _fallback_matbench()

    df = _filter_and_enrich(raw_records_gen)
    _validate_row_count(df)
    _write_parquet(df)

if __name__ == "__main__":
    main()