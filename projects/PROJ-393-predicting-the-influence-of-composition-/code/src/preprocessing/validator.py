"""
Validator for alloy compositions against the periodic table.

Checks for elements not present in the loaded elemental properties dataset
and logs warnings. This ensures data integrity before feature engineering.
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple

import pandas as pd

from src.utils.periodic_table_loader import load_elemental_properties
from src.utils.logging_config import setup_logging

# Configure logger
logger = setup_logging(__name__)


def extract_elements_from_composition(composition_str: str) -> Set[str]:
    """
    Extract unique element symbols from a composition string.
    
    Handles formats like "Co2MnGa", "Co:Mn:Ga", "Co2Mn0.5Ga0.5", etc.
    Assumes standard chemical notation: Capital letter followed by optional lowercase.
    
    Args:
        composition_str: The composition string (e.g., "Co2MnGa")
        
    Returns:
        Set of element symbols found in the string
    """
    if not isinstance(composition_str, str):
        return set()
        
    # Regex to match element symbols: Capital letter followed by optional lowercase
    # This matches standard chemical symbols (e.g., Co, Mn, Ga, Fe)
    pattern = r'([A-Z][a-z]?)'
    matches = re.findall(pattern, composition_str)
    
    # Filter out matches that are not valid chemical symbols if necessary,
    # but here we assume the input is reasonably well-formed.
    # We return all matches as potential elements to be checked against the table.
    return set(matches)


def validate_compositions(
    df: pd.DataFrame,
    composition_column: str = 'composition',
    allowed_elements: Optional[Dict[str, Dict]] = None,
    strict: bool = False
) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    Validate that all elements in the composition column exist in the periodic table data.
    
    Args:
        df: DataFrame containing alloy data
        composition_column: Name of the column containing composition strings
        allowed_elements: Optional pre-loaded elemental properties dict. 
                          If None, loads from data/raw/elemental_properties.csv.
        strict: If True, raise an error if unknown elements are found. 
                If False, log warnings and continue.
                
    Returns:
        Tuple of (validated_df, list_of_warnings)
        
    Raises:
        ValueError: If strict=True and unknown elements are found
    """
    if allowed_elements is None:
        allowed_elements = load_elemental_properties()
        
    known_elements = set(allowed_elements.keys())
    warnings = []
    unknown_elements_found = set()
    
    if composition_column not in df.columns:
        logger.error(f"Composition column '{composition_column}' not found in DataFrame")
        raise ValueError(f"Column '{composition_column}' not found in DataFrame")
        
    for idx, row in df.iterrows():
        comp_str = row[composition_column]
        if pd.isna(comp_str) or not isinstance(comp_str, str):
            continue
            
        elements = extract_elements_from_composition(comp_str)
        unknown = elements - known_elements
        
        if unknown:
            unknown_elements_found.update(unknown)
            warning_msg = (
                f"Row {idx}: Composition '{comp_str}' contains unknown elements: {sorted(unknown)}. "
                f"Known elements: {sorted(known_elements)}. "
                f"Pipeline will proceed with available data, but feature calculation may fail or be incomplete."
            )
            warnings.append({
                "row_index": idx,
                "composition": comp_str,
                "unknown_elements": list(unknown),
                "message": warning_msg
            })
            logger.warning(warning_msg)
            
    if unknown_elements_found:
        logger.warning(
            f"Validation complete. Found {len(unknown_elements_found)} unknown elements: "
            f"{sorted(unknown_elements_found)}. "
            f"Total warnings: {len(warnings)}."
        )
        
        if strict:
            raise ValueError(
                f"Strict validation failed. Unknown elements found: {sorted(unknown_elements_found)}. "
                f"Please update data/raw/elemental_properties.csv or fix the input data."
            )
    else:
        logger.info("Validation complete. All elements found in the periodic table dataset.")
        
    return df, warnings


def main():
    """
    Main entry point for running the validator as a script.
    Expects a CSV file path as a command-line argument or uses default paths.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate alloy compositions against periodic table.")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/processed/alloys_raw.csv",
        help="Path to the input CSV file to validate"
    )
    parser.add_argument(
        "--composition-col",
        type=str,
        default="composition",
        help="Name of the column containing composition strings"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Raise an error if unknown elements are found"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save a JSON report of validation warnings (optional)"
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return 1
        
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows from {input_path}")
        
        validated_df, warnings = validate_compositions(
            df, 
            composition_column=args.composition_col,
            strict=args.strict
        )
        
        if warnings:
            logger.warning(f"Validation completed with {len(warnings)} warnings.")
            
            if args.output:
                import json
                output_path = Path(args.output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w') as f:
                    json.dump(warnings, f, indent=2)
                logger.info(f"Validation warnings saved to {output_path}")
        else:
            logger.info("Validation completed successfully with no warnings.")
            
        return 0
        
    except Exception as e:
        logger.error(f"Validation failed with error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
