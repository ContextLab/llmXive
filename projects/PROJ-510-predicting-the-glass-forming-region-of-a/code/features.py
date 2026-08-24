import logging
import sys
import os
from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd

def get_element_properties(symbol: str) -> Dict[str, float]:
    """
    Retrieves elemental properties (atomic size, electronegativity) from the Mendeleev library.
    Handles potential exceptions if an element is not found.
    """
    try:
        element = mendeleev.element(symbol)
        return {
            "atomic_size": element.atomic_radius,
            "electronegativity": element.electronegativity
        }
    except ValueError:
        logging.error(f"Element '{symbol}' not found in Mendeleev.")
        return {"atomic_size": 0.0, "electronegativity": 0.0}

def validate_composition(composition: str) -> bool:
    """
    Validates the composition string to ensure it contains only valid element symbols separated by commas.
    """
    elements = composition.split(",")
    for element in elements:
        try:
            mendeleev.element(element.strip())  # Check if symbol is valid
        except ValueError:
            return False
    return True

def calculate_mixing_enthalpy(composition: List[str], weights: List[float]) -> float:
    """
    Calculates the mixing enthalpy of a ternary alloy based on elemental properties and composition weights.
    """
    total_enthalpy = 0.0
    for i, element in enumerate(composition):
        properties = get_element_properties(element)
        total_enthalpy += weights[i] * properties["electronegativity"]  # Simplified calculation
    return total_enthalpy

def calculate_atomic_size_mismatch(composition: List[str], weights: List[float]) -> float:
    """
    Calculates the atomic size mismatch of a ternary alloy.
    """
    total_size_mismatch = 0.0
    for i, element in enumerate(composition):
        properties = get_element_properties(element)
        total_size_mismatch += weights[i] * properties["atomic_size"]

    return total_size_mismatch

def calculate_electronegativity_variance(composition: List[str], weights: List[float]) -> float:
    """Calculates the variance of electronegativity values within a composition."""
    electronegativities = []
    for element in composition:
        properties = get_element_properties(element)
        electronegativities.append(properties["electronegativity"])

    weighted_electronegativities = [w * e for w, e in zip(weights, electronegativities)]
    mean_electronegativity = np.mean(weighted_electronegativities)
    variance = np.sum(np.square([x - mean_electronegativity for x in weighted_electronegativities])) / len(composition)
    return variance

def parse_composition(composition: str) -> Tuple[List[str], List[float]]:
    """Parses the composition string into a list of elements and their weights."""
    elements = []
    weights = []
    parts = composition.split(",")
    total_weight = 0.0
    for part in parts:
        element, weight_str = part.strip().split(":")
        weight = float(weight_str)
        elements.append(element)
        weights.append(weight)
        total_weight += weight

    # Normalize weights to sum to 1.0
    normalized_weights = [w / total_weight for w in weights]

    return elements, normalized_weights

def compute_features(row: pd.Series) -> pd.Series:
    """Computes thermodynamic features for a given alloy record."""
    composition = row["composition"]
    try:
        elements, weights = parse_composition(composition)
        if not validate_composition(composition):
            logging.warning(f"Invalid composition: {composition}")
            return pd.Series([np.nan] * 4, index=["mixing_enthalpy", "atomic_size_mismatch", "electronegativity_variance", "valid"])

        mixing_enthalpy = calculate_mixing_enthalpy(elements, weights)
        atomic_size_mismatch = calculate_atomic_size_mismatch(elements, weights)
        electronegativity_variance = calculate_electronegativity_variance(elements, weights)
        return pd.Series([mixing_enthalpy, atomic_size_mismatch, electronegativity_variance, True], index=["mixing_enthalpy", "atomic_size_mismatch", "electronegativity_variance", "valid"])

    except Exception as e:
        logging.error(f"Error processing composition {composition}: {e}")
        return pd.Series([np.nan] * 4, index=["mixing_enthalpy", "atomic_size_mismatch", "electronegativity_variance", "valid"])

def validate_features(df: pd.DataFrame, tolerance: float = 1e-6) -> bool:
    """Validates that the computed features are within a reasonable range."""
    if df["mixing_enthalpy"].isnull().any():
        return False
    if df["atomic_size_mismatch"].isnull().any():
        return False
    if df["electronegativity_variance"].isnull().any():
        return False

    # Add more validation checks as needed (e.g., range limits)

    return True

def run_features(df: pd.DataFrame, output_path: str):
  """Applies feature computation and saves the result to a CSV file."""
  df["features"] = df.apply(compute_features, axis=1)
  df = pd.concat([df, df["features"].apply(pd.Series)], axis=1)
  df = df.drop("features", axis=1)

  if not validate_features(df):
    logging.error("Feature validation failed.")
    raise ValueError("Feature validation failed.")

  df.to_csv(output_path, index=False)
  logging.info(f"Processed data saved to {output_path}")

import mendeleev  # Import inside the function to avoid top-level import issues during testing
