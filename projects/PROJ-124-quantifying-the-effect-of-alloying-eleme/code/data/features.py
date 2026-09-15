import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
import pandas as pd
import numpy as np
from pymatgen.core.periodic_table import Element
from config.elements import get_abundant_elements

logger = logging.getLogger(__name__)

def get_element_properties(element_symbol: str) -> Optional[Dict[str, float]]:
    """
    Retrieves atomic radius and electronegativity for a given element symbol.
    Returns None if the element is not found.
    """
    try:
        element = Element(element_symbol)
        atomic_radius = element.atomic_radius
        electronegativity = element.electronegativity
        return {"atomic_radius": atomic_radius, "electronegativity": electronegativity}
    except KeyError:
        logger.warning(f"Element '{element_symbol}' not found in pymatgen.")
        return None

def parse_composition_string(composition: str) -> List[str]:
    """
    Parses a composition string (e.g., "Fe0.8Ni0.2") into a list of element symbols.
    """
    elements = []
    parts = composition.split()
    for part in parts:
        symbol = part.strip()
        elements.append(symbol)
    return elements

def compute_weighted_mean(values: List[float], weights: List[float]) -> float:
    """
    Computes the weighted mean of a list of values.
    """
    return np.average(values, weights=weights)

def compute_size_mismatch(radius1: float, radius2: float) -> float:
    """
    Computes the size mismatch between two atomic radii.
    """
    return abs(radius1 - radius2)

def compute_pairwise_size_mismatch(composition: List[str], element_properties: Dict[str, Dict[str, float]]) -> List[float]:
    """
    Computes the pairwise size mismatch for all unique pairs of elements in a composition.
    """
    mismatches = []
    for i in range(len(composition)):
        for j in range(i + 1, len(composition)):
            symbol1 = composition[i]
            symbol2 = composition[j]
            if symbol1 in element_properties and symbol2 in element_properties:
                radius1 = element_properties[symbol1]["atomic_radius"]
                radius2 = element_properties[symbol2]["atomic_radius"]
                mismatches.append(compute_size_mismatch(radius1, radius2))
            else:
                logger.warning(f"Properties not found for elements {symbol1} or {symbol2}")
                return []
    return mismatches

def compute_features(row: pd.Series) -> Dict[str, Any]:
    """
    Computes the features for a single row in the DataFrame.
    """
    composition = row["composition"]
    log10_Rc = row["log10_Rc"]
    elements = parse_composition_string(composition)
    element_properties = {}
    atomic_radii = []
    electronegativities = []
    total_weight = 0.0

    for element in elements:
        properties = get_element_properties(element)
        if properties:
            element_properties[element] = properties
            atomic_radii.append(properties["atomic_radius"])
            electronegativities.append(properties["electronegativity"])
            total_weight += 1.0

    if not element_properties:
        logger.warning(f"No valid elements found in composition: {composition}")
        return {}

    atomic_radius_mean = compute_weighted_mean(atomic_radii, [1.0 / total_weight] * len(atomic_radii))
    electronegativity_mean = compute_weighted_mean(electronegativities, [1.0 / total_weight] * len(electronegativities))
    vec_avg = atomic_radius_mean  # Simplified VEC calculation

    pairwise_size_mismatches = compute_pairwise_size_mismatch(elements, element_properties)
    if len(elements) == 3:
      pairwise_size_mismatch_1 = pairwise_size_mismatches[0] if len(pairwise_size_mismatches) > 0 else np.nan
      pairwise_size_mismatch_2 = pairwise_size_mismatches[1] if len(pairwise_size_mismatches) > 1 else np.nan
    else:
      pairwise_size_mismatch_1 = np.nan
      pairwise_size_mismatch_2 = np.nan

    return {
        "atomic_radius_mean": atomic_radius_mean,
        "electronegativity_mean": electronegativity_mean,
        "VEC_avg": vec_avg,
        "size_mismatch": np.nan,
        "pairwise_size_mismatch_1": pairwise_size_mismatch_1,
        "pairwise_size_mismatch_2": pairwise_size_mismatch_2
    }

def main():
    """
    Main function to load data, compute features, and save the processed data.
    """
    try:
        df = pd.read_csv("data/raw/gfa_dataset.csv")
        df["features"] = df.apply(compute_features, axis=1)
        df = pd.concat([df.drop(columns=["features"]), df["features"].apply(pd.Series)], axis=1)
        df.to_csv("data/processed/features.csv", index=False)
        logger.info("Features computed and saved to data/processed/features.csv")
    except FileNotFoundError:
        logger.error("Input file data/raw/gfa_dataset.csv not found.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()