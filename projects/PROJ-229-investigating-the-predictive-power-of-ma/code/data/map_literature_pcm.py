"""
map_literature_pcm.py

This script maps literature phase‑change material (PCM) entries to Materials Project
IDs (MP IDs). It reads the raw literature PCM CSV produced by
`fetch_literature_pcm.py`, queries the Materials Project database for a matching
entry, and writes a new CSV that includes the resolved MP IDs.

Output:
    data/external/literature_pcms_mapped.csv
"""

import logging
import os
from pathlib import Path
from typing import Optional

import pandas as pd
from pymatgen.core import Composition

# mp-api provides a lightweight REST client for the Materials Project.
# It respects the API key supplied via the ``MP_API_KEY`` environment variable
# or via the project's ``config.yaml`` (exposed through ``config.get_api_key``).
from mp_api.client import MPRester

from config import get_api_key
from utils.logger import get_pipeline_logger, log_info, log_error


# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #

def _get_mprester() -> MPRester:
    """
    Initialise an MPRester instance using the API key from ``config.yaml``.

    Raises:
        RuntimeError: If the API key is missing.
    """
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError(
            "Materials Project API key not found. Please set it in config.yaml "
            "under the key ``mp_api_key`` or export the ``MP_API_KEY`` "
            "environment variable."
        )
    return MPRester(api_key)


def load_raw_literature_data() -> pd.DataFrame:
    """
    Load the raw literature PCM data produced by ``fetch_literature_pcm.py``.

    Returns:
        pd.DataFrame: DataFrame containing at least a ``formula`` column.

    Raises:
        FileNotFoundError: If the raw CSV does not exist.
    """
    raw_path = Path("data/external/literature_pcms_raw.csv")
    if not raw_path.is_file():
        raise FileNotFoundError(f"Raw literature PCM file not found: {raw_path}")
    df = pd.read_csv(raw_path)
    if "formula" not in df.columns:
        raise ValueError(
            "Expected column ``formula`` in raw literature PCM CSV."
        )
    return df


def _query_mp_id(composition: str, mpr: MPRester) -> Optional[str]:
    """
    Query the Materials Project for a material matching the given composition.

    The query is performed against the ``pretty_formula`` field.  If multiple
    matches are found, the first one (arbitrarily) is returned.

    Args:
        composition (str): Chemical formula (e.g. ``\"NaCl\"``).
        mpr (MPRester): An instantiated Materials Project REST client.

    Returns:
        Optional[str]: The Materials Project ``material_id`` (e.g. ``mp-1234``)
        if a match is found, otherwise ``None``.
    """
    # Normalise the formula using pymatgen to ensure consistent formatting.
    try:
        comp = Composition(composition)
        pretty = comp.reduced_formula
    except Exception as exc:
        log_error(f"Failed to parse formula '{composition}': {exc}")
        return None

    try:
        results = mpr.summary.search(
            criteria={"pretty_formula": pretty},
            fields=["material_id"],
            # ``limit`` = 1 to avoid large payloads.
            limit=1,
        )
        if results:
            return results[0]["material_id"]
    except Exception as exc:
        log_error(f"Materials Project query failed for '{pretty}': {exc}")
    return None


def map_to_materials_project(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a ``material_id`` column to the dataframe by querying the Materials
    Project for each entry's formula.

    Args:
        df (pd.DataFrame): Input dataframe with a ``formula`` column.

    Returns:
        pd.DataFrame: Dataframe with an additional ``material_id`` column.
    """
    logger = get_pipeline_logger(__name__)
    mpr = _get_mprester()

    material_ids = []
    for idx, row in df.iterrows():
        formula = str(row["formula"])
        logger.debug(f"Mapping formula {formula} (row {idx})")
        mp_id = _query_mp_id(formula, mpr)
        material_ids.append(mp_id)
        if mp_id:
            log_info(f"Mapped {formula} → {mp_id}")
        else:
            log_warning(f"No MP entry found for formula {formula}")

    df = df.copy()
    df["material_id"] = material_ids
    return df


def save_mapped_csv(df: pd.DataFrame) -> None:
    """
    Persist the mapped dataframe to ``data/external/literature_pcms_mapped.csv``.

    Args:
        df (pd.DataFrame): Dataframe containing the ``material_id`` column.
    """
    out_path = Path("data/external/literature_pcms_mapped.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    log_info(f"Mapped literature PCM data written to {out_path}")


# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #

def main() -> None:
    """
    Orchestrates the mapping workflow:
    1. Load raw literature PCM data.
    2. Map each entry to a Materials Project ID.
    3. Save the enriched CSV.
    """
    logger = get_pipeline_logger(__name__)
    try:
        logger.info("Starting literature PCM → MP ID mapping")
        raw_df = load_raw_literature_data()
        mapped_df = map_to_materials_project(raw_df)
        save_mapped_csv(mapped_df)
        logger.info("Mapping completed successfully")
    except Exception as exc:
        log_error(f"Mapping failed: {exc}")
        raise


if __name__ == "__main__":
    main()