"""
Module to map alloy compositions to 'alloy_system' strings.

Logic:
1. Parse the composition string to extract elements and their stoichiometric ratios.
2. Identify the most abundant element (highest stoichiometric coefficient) as the base.
3. Identify secondary elements.
4. Sort secondary elements in Hill order (C first, then H, then alphabetical).
5. Construct the string: 'Base-Secondary1-Secondary2-...'

Example:
Input: "Zr50Cu40Al10" -> Output: "Zr-Cu-Al"
Input: "C100" -> Output: "C"
Input: "H2O" -> Output: "O-H" (O is 1, H is 2? Wait, H2O: H=2, O=1. Base=H. Secondary=O. Hill order for secondary: O. Result: "H-O")
Note: Standard Hill order for the whole string puts C first, then H, then others.
For the *secondary* list in "Base-Secondary...", we sort the secondary elements.
If Base is C, secondary are sorted Hill.
If Base is not C, secondary are sorted Hill (C first if present, then H, then alpha).

This function is designed to be used as a vectorized operation on a pandas DataFrame column.
"""

import re
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple

# Constants for Hill ordering
HILL_ORDER = {'C': 0, 'H': 1}
# Default order for other elements (alphabetical)
# We will use a tuple: (is_C, is_H, element_name) for sorting

def parse_composition_to_dict(composition: str) -> Dict[str, float]:
    """
    Parse a chemical formula string into a dictionary of {element: count}.
    Handles standard chemical notation (e.g., "Zr50Cu40Al10", "H2O", "C6H12O6").
    Assumes elements are followed by numbers; if no number, count is 1.
    Handles multi-letter element symbols (e.g., "Cu", "Zr").
    """
    if not isinstance(composition, str) or not composition.strip():
        return {}

    # Regex to match element symbols (Capital + optional lowercase) followed by optional number
    # Element symbols: [A-Z][a-z]?
    # Number: \d+
    pattern = re.compile(r'([A-Z][a-z]?)(\d*)')
    matches = pattern.findall(composition)

    result = {}
    for element, count_str in matches:
        count = float(count_str) if count_str else 1.0
        result[element] = count

    return result

def get_hill_sort_key(element: str) -> Tuple[int, int, str]:
    """
    Returns a sort key for an element based on Hill system rules.
    (0 if C, 1 if H, 2 otherwise).
    Within groups, sort alphabetically.
    """
    if element == 'C':
        return (0, 0, element)
    elif element == 'H':
        return (1, 0, element)
    else:
        return (2, 0, element)

def map_to_alloy_system(composition: str) -> str:
    """
    Maps a single composition string to an alloy system string.

    Steps:
    1. Parse composition to {element: count}.
    2. Find element with max count -> Base.
    3. Remaining elements -> Secondaries.
    4. Sort Secondaries by Hill order.
    5. Join: f"{Base}-{Secondary1}-{Secondary2}..."
    """
    if not isinstance(composition, str) or not composition.strip():
        return "Unknown"

    elements = parse_composition_to_dict(composition)

    if not elements:
        return "Unknown"

    # Find the most abundant element (Base)
    # If there's a tie, pick the one that comes first alphabetically (or Hill order) for determinism?
    # The spec says "Identify most abundant element as base".
    # If tie, we'll sort by Hill order to pick the "primary" one if needed, but usually ties are rare or handled by stable sort.
    # Let's sort items by (-count, hill_key) to get the base.
    sorted_elements = sorted(
        elements.items(),
        key=lambda x: (-x[1], get_hill_sort_key(x[0]))
    )

    base_element = sorted_elements[0][0]
    secondary_elements = [e[0] for e in sorted_elements[1:]]

    # Sort secondary elements in Hill order
    secondary_elements.sort(key=get_hill_sort_key)

    if not secondary_elements:
        return base_element

    return f"{base_element}-{'-'.join(secondary_elements)}"

def add_alloy_system_column(df: pd.DataFrame, composition_col: str = 'composition', output_col: str = 'alloy_system') -> pd.DataFrame:
    """
    Adds an 'alloy_system' column to the dataframe based on the composition column.

    Args:
        df: Input DataFrame.
        composition_col: Name of the column containing composition strings.
        output_col: Name of the new column to create.

    Returns:
        DataFrame with the new column added.
    """
    if composition_col not in df.columns:
        raise ValueError(f"Column '{composition_col}' not found in DataFrame. Available: {list(df.columns)}")

    df[output_col] = df[composition_col].apply(map_to_alloy_system)
    return df

def main():
    """
    Standalone execution for testing or direct file processing.
    Expects a CSV file at data/processed/filtered_properties.csv (from T017a).
    Outputs to data/processed/alloy_system_mapped.csv.
    """
    import os
    import sys
    import logging
    from pathlib import Path

    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # Define paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    input_path = project_root / 'data' / 'processed' / 'filtered_properties.csv'
    output_path = project_root / 'data' / 'processed' / 'alloy_system_mapped.csv'

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    logger.info(f"Loading data from {input_path}")
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to load input file: {e}")
        sys.exit(1)

    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")

    logger.info("Mapping compositions to alloy systems...")
    try:
        df = add_alloy_system_column(df, composition_col='composition', output_col='alloy_system')
    except Exception as e:
        logger.error(f"Failed to map alloy systems: {e}")
        sys.exit(1)

    logger.info(f"Mapping complete. Unique alloy systems: {df['alloy_system'].nunique()}")
    logger.info(f"Saving to {output_path}")

    try:
        df.to_csv(output_path, index=False)
        logger.info("Successfully saved output file.")
    except Exception as e:
        logger.error(f"Failed to save output file: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
