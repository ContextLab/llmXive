import os
import sys
import logging
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

from config import get_config, random_seed
from utils.logging_config import log_info_with_context, log_error_with_context

logger = logging.getLogger(__name__)

# Set random seed for reproducibility
np.random.seed(random_seed)

def get_periodic_property(element: str, property_name: str) -> float:
    """
    Fetches a periodic property for an element.
    Uses mendeleev if available, otherwise falls back to hardcoded defaults.
    """
    try:
        from mendeleev import element as mendeleev_element
        el = mendeleev_element(element)
        if hasattr(el, property_name):
            val = getattr(el, property_name)
            return val if val is not None else 0.0
        return 0.0
    except ImportError:
        # Fallback values if mendeleev not available
        fallbacks = {
            'atomic_radius': 1.5,
            'electronegativity': 2.0,
            'atomic_number': 1,
            'group': 1,
            'period': 2
        }
        return fallbacks.get(property_name, 0.0)
    except Exception:
        return 0.0

def encode_composition(composition_str: str) -> Tuple[List[float], List[float], List[float]]:
    """
    Encodes a composition string into elemental fractions and periodic descriptors.
    Returns: (elemental_fractions, atomic_radii, electronegativities)
    """
    # Parse composition string (e.g., "Fe2O3" -> {"Fe": 2, "O": 3})
    import re
    pattern = re.compile(r"([A-Z][a-z]?)(\d*)")
    matches = pattern.findall(composition_str)
    
    elements = {}
    total_atoms = 0
    
    for elem, count in matches:
        count = int(count) if count else 1
        elements[elem] = count
        total_atoms += count
    
    if total_atoms == 0:
        return [], [], []
    
    # Calculate fractions and descriptors
    fractions = []
    radii = []
    electronegativities = []
    
    for elem, count in elements.items():
        frac = count / total_atoms
        fractions.append(frac)
        radii.append(get_periodic_property(elem, 'atomic_radius'))
        electronegativities.append(get_periodic_property(elem, 'electronegativity'))
    
    return fractions, radii, electronegativities

def validate_periodic_descriptors(radii: List[float], electronegativities: List[float]) -> bool:
    """
    Validates that periodic descriptors are present and valid.
    Returns True if at least two descriptors per element are available.
    """
    if len(radii) < 2 or len(electronegativities) < 2:
        return False
    if any(r <= 0 for r in radii) or any(e <= 0 for e in electronegativities):
        return False
    return True

def encode_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encodes the composition column in the DataFrame.
    Adds elemental fractions and periodic descriptors as new columns.
    """
    log_info_with_context("Starting composition encoding", context="feature_encoder")
    
    encoded_data = []
    
    for idx, row in df.iterrows():
        comp = row["composition"]
        fractions, radii, electronegativities = encode_composition(comp)
        
        if not validate_periodic_descriptors(radii, electronegativities):
            log_error_with_context(
                f"Invalid periodic descriptors for {comp}",
                context="feature_encoder"
            )
            continue
        
        encoded_row = {
            "composition": comp,
            "bulk_modulus": row["bulk_modulus"],
            "shear_modulus": row["shear_modulus"]
        }
        
        # Add elemental fractions (up to 10 elements max for fixed dimensionality)
        for i, frac in enumerate(fractions[:10]):
            encoded_row[f"elem_frac_{i}"] = frac
        
        # Add periodic descriptors
        for i, rad in enumerate(radii[:10]):
            encoded_row[f"atomic_radius_{i}"] = rad
        
        for i, ele in enumerate(electronegativities[:10]):
            encoded_row[f"electronegativity_{i}"] = ele
        
        encoded_data.append(encoded_row)
    
    encoded_df = pd.DataFrame(encoded_data)
    log_info_with_context(f"Encoded {len(encoded_df)} compositions", context="feature_encoder")
    return encoded_df

def save_encoded_data(df: pd.DataFrame, output_path: str):
    """Saves the encoded DataFrame to CSV."""
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    df.to_csv(output_path, index=False)
    log_info_with_context(f"Saved encoded data to {output_path}", context="feature_encoder")

def main():
    """Main entry point for feature encoding."""
    from data_ingestion import load_oqmd_data, filter_valid_entries
    
    config = get_config()
    processed_dir = config.get("processed_dir", "data/processed")
    input_path = os.path.join(processed_dir, "encoded_alloys.csv")
    
    if not os.path.exists(input_path):
        log_error_with_context(f"Input file not found: {input_path}", context="feature_encoder")
        return 1
    
    try:
        df = pd.read_csv(input_path)
        encoded_df = encode_dataframe(df)
        save_encoded_data(encoded_df, input_path)  # Overwrite with encoded version
        log_info_with_context("Feature encoding completed successfully", context="feature_encoder")
        return 0
    except Exception as e:
        log_error_with_context(f"Feature encoding failed: {str(e)}", context="feature_encoder")
        return 1

if __name__ == "__main__":
    sys.exit(main())
