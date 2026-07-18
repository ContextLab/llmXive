import os
import sys
import logging
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

from mendeleev import element as mendeleev_element
from utils.logging_config import get_logger, log_error_with_context, log_info_with_context

logger = get_logger(__name__)

# Standard periodic properties used as descriptors
PERIODIC_DESCRIPTORS = [
    "atomic_radius",
    "electronegativity",
    "melting_point",
    "boiling_point",
    "density",
    "atomic_weight",
    "group",
    "period",
    "electrons_per_shell",
    "ionization_energy"
]

def get_periodic_property(symbol: str, property_name: str) -> Optional[float]:
    """
    Fetch a periodic property for a given element symbol using mendeleev.
    Returns None if the element or property is not found.
    """
    try:
        el = mendeleev_element(symbol)
        if property_name == "electrons_per_shell":
            # mendeleev stores this as a list/string, convert to sum or specific
            val = el.electrons_per_shell
            if isinstance(val, list):
                return float(sum(val))
            return float(val) if val is not None else None
        
        val = getattr(el, property_name, None)
        if val is None:
            return None
        return float(val)
    except Exception as e:
        log_error_with_context(logger, f"Failed to fetch {property_name} for {symbol}: {e}")
        return None

def encode_composition(composition_str: str) -> Tuple[Dict[str, float], Dict[str, Dict[str, float]]]:
    """
    Parses a composition string (e.g., "Fe0.5Ni0.5") and returns:
    1. A flat dict of elemental fractions { "Fe": 0.5, "Ni": 0.5 }
    2. A dict of periodic descriptors per element { "Fe": { "atomic_radius": 126.0, ... } }
    
    Raises ValueError if composition is invalid or missing required descriptors.
    """
    if not composition_str:
        raise ValueError("Empty composition string")

    elements = []
    fractions = []
    
    # Simple parser for standard composition strings (SymbolFraction...)
    # Handles cases like "Fe0.5Ni0.5", "Fe50Ni50" (assuming normalized or simple parsing)
    # We assume the input is normalized or follows standard format from OQMD
    import re
    pattern = r"([A-Z][a-z]*)(\d+\.?\d*|\d*\.?\d+)"
    matches = re.findall(pattern, composition_str)
    
    if not matches:
        # Fallback for integer percentages if no decimals, or malformed
        # Attempt to handle "Fe50Ni50" -> Fe:50, Ni:50 -> normalize
        pattern_int = r"([A-Z][a-z]*)(\d+)"
        matches_int = re.findall(pattern_int, composition_str)
        if matches_int:
            matches = [(m[0], float(m[1])) for m in matches_int]
        else:
            raise ValueError(f"Could not parse composition: {composition_str}")

    total = sum(float(m[1]) for m in matches)
    
    if total == 0:
        raise ValueError("Total composition sum is zero")

    descriptors_map = {}
    
    for symbol, frac in matches:
        frac_norm = float(frac) / total
        elements.append(symbol)
        fractions.append(frac_norm)
        
        # Fetch descriptors
        elem_desc = {}
        missing_desc = []
        for prop in PERIODIC_DESCRIPTORS:
            val = get_periodic_property(symbol, prop)
            if val is not None:
                elem_desc[prop] = val
            else:
                missing_desc.append(prop)
        
        # Validation: Ensure at least two periodic descriptors per element
        if len(elem_desc) < 2:
            raise ValueError(
                f"Element {symbol} in composition '{composition_str}' "
                f"has only {len(elem_desc)} valid periodic descriptors (minimum 2 required). "
                f"Missing: {missing_desc}"
            )
        
        descriptors_map[symbol] = elem_desc

    return dict(zip(elements, fractions)), descriptors_map

def encode_dataframe(df: pd.DataFrame, composition_col: str = "composition") -> pd.DataFrame:
    """
    Adds encoded features to the dataframe.
    - Adds columns for elemental fractions (one-hot style for elements present)
    - Adds columns for periodic descriptors (weighted by fraction)
    
    Validates that every element has >= 2 descriptors.
    """
    logger.info(f"Encoding composition column: {composition_col}")
    
    all_elements = set()
    element_fractions = []
    element_descriptors = []
    
    for idx, row in df.iterrows():
        try:
            comp_str = row[composition_col]
            fractions, descriptors = encode_composition(comp_str)
            
            all_elements.update(fractions.keys())
            element_fractions.append(fractions)
            element_descriptors.append(descriptors)
        except ValueError as e:
            log_error_with_context(logger, f"Skipping row {idx}: {e}")
            # Replace with NaN or drop? We'll set to NaN for now to keep index
            element_fractions.append({})
            element_descriptors.append({})

    # Create columns for elemental fractions
    for elem in sorted(all_elements):
        col_name = f"frac_{elem}"
        df[col_name] = [row.get(elem, 0.0) for row in element_fractions]

    # Create columns for weighted periodic descriptors
    # We compute: Sum(frac_i * descriptor_i) for each descriptor
    for prop in PERIODIC_DESCRIPTORS:
        col_name = f"weighted_{prop}"
        values = []
        for f_dict, d_dict in zip(element_fractions, element_descriptors):
            weighted_sum = 0.0
            for elem, frac in f_dict.items():
                if elem in d_dict and prop in d_dict[elem]:
                    weighted_sum += frac * d_dict[elem][prop]
            values.append(weighted_sum)
        df[col_name] = values

    # Validation Check: Ensure no rows were silently dropped or had insufficient data
    # The encode_composition function already raises ValueError if < 2 descriptors.
    # If we reached here, all processed rows passed.
    # We verify that the resulting dataframe has the expected descriptor columns
    expected_desc_cols = [f"weighted_{p}" for p in PERIODIC_DESCRIPTORS]
    missing_cols = [c for c in expected_desc_cols if c not in df.columns]
    
    if missing_cols:
        log_error_with_context(logger, f"Missing expected descriptor columns: {missing_cols}")
        raise RuntimeError(f"Feature encoding failed: Missing columns {missing_cols}")

    log_info_with_context(logger, f"Successfully encoded {len(df)} rows with {len(all_elements)} unique elements")
    return df

def save_encoded_data(df: pd.DataFrame, output_path: str):
    """Saves the encoded dataframe to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    log_info_with_context(logger, f"Saved encoded data to {output_path}")

def main():
    """
    Entry point for the feature encoder.
    Expects input from data/processed/intermediate_data.csv (or similar)
    and outputs to data/processed/encoded_alloys.csv
    """
    # Configuration (simplified for this task, usually via config.py)
    input_path = "data/processed/intermediate_data.csv"
    output_path = "data/processed/encoded_alloys.csv"
    
    if not os.path.exists(input_path):
        # Fallback if intermediate doesn't exist, try raw or previous step
        # In a real pipeline, this would be passed via CLI or config
        log_error_with_context(logger, f"Input file not found: {input_path}")
        sys.exit(1)

    df = pd.read_csv(input_path)
    
    # Run encoding with validation
    try:
        encoded_df = encode_dataframe(df)
        save_encoded_data(encoded_df, output_path)
        print(f"Encoding complete. Output: {output_path}")
    except ValueError as e:
        log_error_with_context(logger, f"Validation failed during encoding: {e}")
        sys.exit(1)
    except Exception as e:
        log_error_with_context(logger, f"Unexpected error during encoding: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
