import os
import sys
import logging
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from mendeleev import element

# Import local utilities if they exist, otherwise define minimal fallbacks
# to ensure the script runs as a standalone unit if needed, but primarily
# we rely on the project structure.
try:
    from utils.logging_config import get_logger
except ImportError:
    # Fallback logger if utils not in path during isolated test
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    def get_logger(name): return logging.getLogger(name)

logger = get_logger(__name__)

# Configuration: Minimum required descriptors per element
MIN_PERIODIC_DESCRIPTORS = 2

def get_periodic_property(symbol: str, property_name: str) -> float:
    """
    Fetch a specific periodic property for an element using mendeleev.
    
    Args:
        symbol: Element symbol (e.g., 'Fe')
        property_name: Name of the property (e.g., 'atomic_radius', 'electronegativity')
    
    Returns:
        float: The property value.
    
    Raises:
        ValueError: If element is not found or property is missing.
    """
    try:
        elem = element(symbol)
        # Mendeleev attribute access
        val = getattr(elem, property_name, None)
        if val is None:
            raise ValueError(f"Property '{property_name}' not found for {symbol}")
        return float(val)
    except Exception as e:
        raise ValueError(f"Failed to fetch {property_name} for {symbol}: {e}")

def encode_composition(composition_str: str) -> Dict[str, List[float]]:
    """
    Encodes a composition string (e.g., 'Fe0.5Ni0.5') into elemental fractions
    and a list of periodic descriptors for each element.
    
    This function ensures that for every element present, we extract at least
    MIN_PERIODIC_DESCRIPTORS properties.
    
    Args:
        composition_str: String representation of composition (e.g., 'Fe0.5Ni0.5')
    
    Returns:
        Dict with 'fractions' (list of floats) and 'descriptors' (list of lists).
    
    Raises:
        ValueError: If an element cannot be resolved or lacks sufficient properties.
    """
    # Simple parser for composition: ElementFraction pairs
    # Assumes format like Fe0.5Ni0.5 or Fe_0.5Ni_0.5. 
    # For robustness, we handle standard chemical formulas with numbers.
    import re
    
    # Pattern to match Element symbol followed by optional number
    # Mendeleev handles element symbols case-sensitively (First upper, rest lower)
    pattern = r'([A-Z][a-z]?)(\d*\.?\d*)'
    matches = re.findall(pattern, composition_str)
    
    if not matches:
        raise ValueError(f"Could not parse composition: {composition_str}")
    
    elements = []
    fractions = []
    
    for sym, frac_str in matches:
        if not frac_str:
            frac_str = "1"
        frac = float(frac_str)
        elements.append(sym)
        fractions.append(frac)
    
    # Normalize fractions to sum to 1.0
    total = sum(fractions)
    if total == 0:
        raise ValueError("Sum of fractions is zero")
    fractions = [f / total for f in fractions]
    
    # Define the periodic descriptors we need (at least 2)
    # We use 'atomic_radius' and 'electronegativity' as standard proxies
    descriptors_to_fetch = ['atomic_radius', 'electronegativity']
    
    if len(descriptors_to_fetch) < MIN_PERIODIC_DESCRIPTORS:
        raise RuntimeError("Configuration error: MIN_PERIODIC_DESCRIPTORS set too high for available properties")
    
    encoded_descriptors = []
    
    for sym in elements:
        elem_row = []
        for prop in descriptors_to_fetch:
            try:
                val = get_periodic_property(sym, prop)
                elem_row.append(val)
            except ValueError:
                # If a specific property is missing, we might want to handle it
                # but per task requirements, we must ensure at least 2 descriptors.
                # If we can't fetch 2, we fail loudly as per constraints.
                raise ValueError(f"Element {sym} missing required property {prop}")
        
        # Validation: Ensure we have at least MIN_PERIODIC_DESCRIPTORS
        if len(elem_row) < MIN_PERIODIC_DESCRIPTORS:
            raise ValueError(
                f"Element {sym} yielded only {len(elem_row)} descriptors, "
                f"but {MIN_PERIODIC_DESCRIPTORS} are required."
            )
        
        encoded_descriptors.append(elem_row)
    
    return {
        'elements': elements,
        'fractions': fractions,
        'descriptors': encoded_descriptors,
        'descriptor_names': descriptors_to_fetch
    }

def validate_periodic_descriptors(encoded_data: Dict[str, Any]) -> bool:
    """
    Validates that the encoded data contains at least MIN_PERIODIC_DESCRIPTORS
    per element.
    
    Args:
        encoded_data: Dictionary containing 'descriptors' (list of lists)
    
    Returns:
        bool: True if valid.
    
    Raises:
        ValueError: If validation fails.
    """
    descriptors = encoded_data.get('descriptors', [])
    if not descriptors:
        raise ValueError("No descriptors found in encoded data")
    
    for i, elem_desc in enumerate(descriptors):
        if len(elem_desc) < MIN_PERIODIC_DESCRIPTORS:
            raise ValueError(
                f"Validation failed: Element at index {i} has {len(elem_desc)} descriptors, "
                f"minimum required is {MIN_PERIODIC_DESCRIPTORS}."
            )
    
    logger.info(f"Validation passed: All elements have >= {MIN_PERIODIC_DESCRIPTORS} descriptors.")
    return True

def encode_dataframe(df: pd.DataFrame, composition_col: str = 'composition') -> pd.DataFrame:
    """
    Encodes a DataFrame of alloys by adding feature columns for elemental fractions
    and periodic descriptors.
    
    Args:
        df: Input DataFrame with a 'composition' column.
        composition_col: Name of the composition column.
    
    Returns:
        DataFrame with new feature columns.
    """
    logger.info(f"Encoding compositions from column: {composition_col}")
    
    all_features = []
    descriptor_names = None
    
    for idx, row in df.iterrows():
        try:
            encoded = encode_composition(row[composition_col])
            
            # Validate immediately after encoding
            validate_periodic_descriptors(encoded)
            
            # Flatten features for this row
            # Format: elem_0_frac, elem_0_desc_0, elem_0_desc_1, elem_1_frac, ...
            # To keep it simple and fixed-width, we assume a max number of elements or
            # we construct dynamic column names. For this implementation, we'll
            # create a fixed set of columns based on the unique elements found in the dataset
            # OR we flatten the list of descriptors and fractions into a single vector
            # if the number of elements is variable, we need a strategy.
            # Strategy: We will create columns for the first N elements found in the dataset
            # or use a generic "element_0", "element_1" approach if the dataset is sorted.
            # However, standard alloy encoding often uses a fixed set of element columns.
            # Given the constraints, we will flatten the descriptors and fractions into
            # a list of floats and store them as a single column 'features' for now,
            # OR expand them into 'elem_0_frac', 'elem_0_rad', 'elem_0_elec', 'elem_1_frac', etc.
            
            # Let's expand dynamically based on the number of elements in the specific row
            # This results in variable columns per row if not handled carefully.
            # Better approach for a CSV: Flatten into a single 'features' list column
            # or ensure the dataset has a consistent max number of elements.
            # We will assume a max of 4 elements for this pipeline or flatten into a list.
            # Let's flatten into a list of floats: [frac0, desc0_0, desc0_1, frac1, desc1_0, desc1_1, ...]
            
            features = []
            for i in range(len(encoded['elements'])):
                features.append(encoded['fractions'][i])
                for d in encoded['descriptors'][i]:
                    features.append(d)
            
            all_features.append(features)
            
            if descriptor_names is None:
                # Construct column names for the first row
                # We don't know the max elements yet, so we'll store the list and
                # later expand if needed, or just keep as a list column.
                # For CSV compatibility, let's create fixed columns if we know the max elements.
                # Since we don't know the global max, we'll store as a JSON string or list.
                # But the task asks for "feature vectors".
                # Let's assume a max of 5 elements for the project scope or flatten to a single string.
                # Actually, let's just create columns: feat_0, feat_1, ... based on the longest row.
                pass
                
        except Exception as e:
            logger.error(f"Error encoding row {idx}: {e}")
            raise
    
    # Create a new column with the flattened features
    df['features'] = all_features
    
    # If we need to expand to columns, we would do it here, but for now
    # we ensure the validation logic is present and the data is encoded.
    # The downstream model training will need to handle the 'features' column.
    
    return df

def save_encoded_data(df: pd.DataFrame, output_path: str):
    """
    Saves the encoded DataFrame to a CSV file.
    
    Args:
        df: Encoded DataFrame.
        output_path: Path to the output CSV.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved encoded data to {output_path}")

def main():
    """
    Main entry point for testing the encoder and validation logic.
    """
    # Create a dummy dataset for testing the validation
    data = {
        'composition': ['Fe0.5Ni0.5', 'Fe0.33Ni0.33Co0.34', 'Al0.5Cu0.5']
    }
    df = pd.DataFrame(data)
    
    try:
        encoded_df = encode_dataframe(df)
        print("Encoding successful. Features:")
        print(encoded_df['features'].tolist())
        print("Validation passed: All elements have >= 2 periodic descriptors.")
    except ValueError as e:
        print(f"Validation Failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
