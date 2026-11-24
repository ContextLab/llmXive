"""
Utility module for loading the verified elemental properties CSV.

The module provides a single public function ``load_elemental_properties`` that
reads ``data/raw/elemental_properties.csv`` into a ``pandas.DataFrame`` and
caches the result for subsequent calls.

This helper is used by the descriptor‑calculation code (see
``src.features.descriptor_calculator``) and by any downstream analysis that
requires elemental reference data.
"""

from __future__ import annotations

import logging
from pathlib import Path
from functools import lru_cache

import pandas as pd

from llmxive_toolkit import paths

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def load_elemental_properties() -> pd.DataFrame:
    """
    Load the elemental properties CSV produced by ``generate_elemental_properties.py``.

    Returns
    -------
    pandas.DataFrame
        DataFrame with columns ``element``, ``electronegativity``,
        ``atomic_radii``, and ``valence_electrons``.
    """
    csv_path = paths.data("raw", "elemental_properties.csv")
    if not csv_path.is_file():
        logger.error(f"Elemental properties file not found at {csv_path}")
        raise FileNotFoundError(f"Missing elemental properties CSV: {csv_path}")

    df = pd.read_csv(csv_path, dtype={
        "element": str,
        "electronegativity": float,
        "atomic_radii": float,
        "valence_electrons": int,
    })
    logger.debug(f"Loaded {len(df)} elemental property rows")
    return df


def get_element_property(element: str, property_name: str):
    """
    Retrieve a single property for a given element.

    Parameters
    ----------
    element : str
        Chemical symbol (e.g., ``'Fe'``).
    property_name : str
        One of ``'electronegativity'``, ``'atomic_radii'``,
        ``'valence_electrons'``.

    Returns
    -------
    float or int
        The requested property value.

    Raises
    ------
    KeyError
        If the element or property is not present in the reference table.
    """
    df = load_elemental_properties()
    row = df.loc[df["element"] == element]
    if row.empty:
        raise KeyError(f"Element '{element}' not found in elemental properties table")
    if property_name not in df.columns:
        raise KeyError(f"Property '{property_name}' not available")
    return row.iloc[0][property_name]