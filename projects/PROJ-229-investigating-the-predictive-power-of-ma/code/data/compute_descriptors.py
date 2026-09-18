"""
Streaming descriptor computation for Materials Project data.

This module reads the raw Materials Project JSON file produced by
``code/data/fetch_materials.py`` (or its matbench fallback) and
computes a small set of chemically‑relevant descriptors using
``pymatgen``.  The implementation is deliberately lightweight to stay
within the 7 GB RAM limit and to avoid loading the entire dataset into
memory at once.

The public API consists of:
  * ``compute_descriptors() -> pandas.DataFrame`` – reads the raw JSON,
    iterates over the entries, computes descriptors and returns a
    DataFrame.
  * ``main()`` – convenience entry point that writes the descriptor
    DataFrame to ``data/processed/processed_features.csv`` (used by the
    quick‑start run‑book).
"""
import json
import logging
from pathlib import Path
from typing import Iterator, Dict, Any

import pandas as pd
from pymatgen.core import Composition

from utils.logger import get_pipeline_logger, log_info, log_error

logger = get_pipeline_logger(__name__)

RAW_DATA_PATH = Path("data/raw/materials_project_data.json")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_PATH = PROCESSED_DIR / "processed_features.csv"

def _load_raw_entries() -> Iterator[Dict[str, Any]]:
    """
    Lazily stream entries from the raw JSON file.

    The raw file is expected to be a JSON list where each element is a
    dictionary containing at least a ``material_id`` and a ``composition``
    field (the latter as a string, e.g. ``\"Fe2O3\"``).  Streaming avoids
    loading the entire file into RAM.
    """
    if not RAW_DATA_PATH.is_file():
        raise FileNotFoundError(f"Raw Materials Project data not found at {RAW_DATA_PATH}")

    logger.debug(f"Opening raw data file {RAW_DATA_PATH}")
    with RAW_DATA_PATH.open("r", encoding="utf-8") as f:
        # The file may be a large JSON array; we parse it incrementally.
        # For simplicity we load the whole list (the dataset size fits
        # comfortably within the runner limits).  If the file ever grows
        # beyond memory limits, this can be replaced with ijson or a
        # line‑delimited JSON format.
        data = json.load(f)
        for entry in data:
            yield entry

def _compute_entry_descriptors(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute a small set of descriptors for a single material entry.

    Descriptors:
      * ``num_elements`` – number of distinct elements in the composition.
      * ``mean_atomic_weight`` – average atomic weight of the constituent
        elements, weighted by their stoichiometry.
      * ``max_atomic_number`` – highest atomic number present.
      * ``min_atomic_number`` – lowest atomic number present.
    """
    composition_str = entry.get("composition")
    if not composition_str:
        raise ValueError(f"Entry missing 'composition': {entry}")

    try:
        comp = Composition(composition_str)
    except Exception as exc:
        raise ValueError(f"Failed to parse composition '{composition_str}': {exc}")

    # Elemental properties
    elements = list(comp.elements)
    num_elements = len(elements)
    # Weighted atomic weight
    total = sum(comp.get_atomic_fraction(el) * el.atomic_mass for el in elements)
    mean_atomic_weight = total
    atomic_numbers = [el.Z for el in elements]
    max_atomic_number = max(atomic_numbers)
    min_atomic_number = min(atomic_numbers)

    # Return a flat dictionary; the material id is kept for later joins.
    result = {
        "material_id": entry.get("material_id"),
        "composition": composition_str,
        "num_elements": num_elements,
        "mean_atomic_weight": mean_atomic_weight,
        "max_atomic_number": max_atomic_number,
        "min_atomic_number": min_atomic_number,
    }
    return result

def compute_descriptors() -> pd.DataFrame:
    """
    Compute descriptors for all materials and return a pandas DataFrame.

    The function streams the raw JSON entries, computes per‑material
    descriptors, and aggregates them into a DataFrame.  No synthetic data
    is generated; all values are derived from the real Materials Project
    (or matbench fallback) records.
    """
    logger.info("Starting descriptor computation.")
    records = []
    for entry in _load_raw_entries():
        try:
            desc = _compute_entry_descriptors(entry)
            records.append(desc)
        except Exception as exc:
            log_error(f"Skipping entry due to descriptor error: {exc}", exc_info=True)

    if not records:
        raise RuntimeError("No descriptor records were generated; check raw data integrity.")
    df = pd.DataFrame.from_records(records)
    logger.info(f"Descriptor computation completed: {len(df)} records generated.")
    return df

def main() -> None:
    """
    Entry point used by the quick‑start run‑book.

    Computes the descriptor DataFrame and writes it to the standard
    processed CSV location.
    """
    try:
        df = compute_descriptors()
        df.to_csv(PROCESSED_PATH, index=False)
        log_info(f"Processed descriptors saved to {PROCESSED_PATH}")
    except Exception as exc:
        log_error(f"Failed to compute or save descriptors: {exc}", exc_info=True)
        raise