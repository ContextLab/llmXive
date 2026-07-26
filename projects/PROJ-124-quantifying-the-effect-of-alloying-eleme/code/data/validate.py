import logging
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple, Optional
import pandas as pd
from config.elements import get_abundant_elements_set
from utils.logger import get_logger

logger = get_logger(__name__)

def validate_elements(df: pd.DataFrame, composition_col: str = "composition") -> Tuple[pd.DataFrame, List[str]]:
    """
    Validate elements in the composition column against Pymatgen and the abundant elements list.
    
    This function performs two levels of validation:
    1. Checks if elements are in the predefined abundant elements list.
    2. Attempts to fetch properties from Pymatgen to verify they are valid chemical elements.
    
    Rows containing unknown or invalid elements are excluded from the returned DataFrame.
    Specific warnings are logged for each excluded row.
    
    Args:
        df: Input DataFrame containing composition strings.
        composition_col: Name of the column containing composition strings.
        
    Returns:
      A tuple containing:
          - valid_df: DataFrame with rows containing only valid elements.
          - excluded_ids: List of row indices (or composition IDs) that were excluded.
    """
    logger.info("Starting element validation for dataset.")
    
    abundant_elements = get_abundant_elements_set()
    invalid_rows = []
    valid_rows = []
    
    # Helper to parse composition string into a set of elements
    # Expected format: "Element1:0.33,Element2:0.33,Element3:0.33" or similar
    # We need to extract the element symbols.
    
    def extract_elements(composition_str: str) -> List[str]:
        """Extract element symbols from a composition string."""
        if pd.isna(composition_str):
            return []
        
        # Basic parsing: split by comma, then by colon or space to get element
        # This handles formats like "Al:0.5,Cu:0.5" or "Al Cu"
        elements = []
        parts = str(composition_str).split(',')
        for part in parts:
            part = part.strip()
            if ':' in part:
                elem = part.split(':')[0].strip()
            else:
                # Fallback for space-separated or simple strings
                elem = part.split()[0] if part.split() else part
            if elem:
                elements.append(elem)
        return elements

    try:
        from pymatgen.core import Element
    except ImportError:
        logger.error("Pymatgen is not installed. Cannot validate elements against chemical database.")
        # If pymatgen is missing, we can only check against the abundant list
        # This is a critical dependency for the feature engineering pipeline
        raise ImportError("Pymatgen is required for element validation. Please install it.")

    for idx, row in df.iterrows():
        comp_str = row.get(composition_col)
        if pd.isna(comp_str):
            logger.warning(f"Row {idx} has a missing composition. Excluding.")
            invalid_rows.append(idx)
            continue
        
        elements = extract_elements(comp_str)
        has_unknown = False
        unknown_details = []
        
        for elem_sym in elements:
            # Check against abundant list first (fast)
            if elem_sym not in abundant_elements:
                # It's not in our "abundant" list, but might still be a valid element
                # We need to check Pymatgen to see if it's a real element at all
                try:
                    Element(elem_sym)
                    # It's a valid element, but not in our abundant list.
                    # Depending on strictness, we might flag this, but the task
                    # specifically says "exclude rows with unknown elements".
                    # "Unknown" usually implies not a valid element or not supported.
                    # Let's assume if it's a valid Element, we keep it, but log a warning.
                    # However, the task says "exclude rows with unknown elements".
                    # If the element is not in the abundant list, is it "unknown"?
                    # The spec says: "log specific warnings... exclude that row".
                    # Let's interpret "unknown" as "not in our supported/abundant list"
                    # OR "not a valid element in Pymatgen".
                    # Given the context of "most abundant metallic elements",
                    # elements outside this list are likely not supported by the model.
                    # So we exclude them if they are not in the abundant list.
                    pass 
                except Exception:
                    # Not a valid element in Pymatgen
                    has_unknown = True
                    unknown_details.append(f"{elem_sym} (Invalid element)")
                    break
            
            # If it passed the Pymatgen check, we still check if it's in our abundant list.
            # The task implies we should exclude rows with elements we don't know how to handle.
            # If the element is valid but not abundant, it might be an "unknown" in the context of our model.
            # Let's strictly follow: "If an element is not found in Pymatgen" -> exclude.
            # But also, if it's not in our `elements.yaml` list, it's effectively unknown for our pipeline.
            # Let's combine: Exclude if NOT in abundant_elements OR NOT in Pymatgen.
            if elem_sym not in abundant_elements:
                # Check if it's a valid element just for better logging
                try:
                    Element(elem_sym)
                    unknown_details.append(f"{elem_sym} (Not in abundant list)")
                except Exception:
                    unknown_details.append(f"{elem_sym} (Invalid element)")
                has_unknown = True
                break # Stop checking this row

        if has_unknown:
            invalid_rows.append(idx)
            logger.warning(
                f"Excluding row {idx} (Composition: {comp_str}) due to unknown/unsupported elements: {', '.join(unknown_details)}"
            )
        else:
            valid_rows.append(idx)

    logger.info(f"Validation complete. Excluded {len(invalid_rows)} rows. Kept {len(valid_rows)} rows.")
    
    valid_df = df.iloc[valid_rows].reset_index(drop=True)
    return valid_df, invalid_rows

def main():
    """Main entry point for running validation on the processed features file."""
    logger.info("Running element validation in main().")
    
    # Determine paths
    project_root = Path(__file__).resolve().parent.parent.parent
    input_path = project_root / "data" / "processed" / "features.csv"
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.info("Skipping validation. Ensure T014 (features.py) has run successfully.")
        return

    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows from {input_path}")
    except Exception as e:
        logger.error(f"Failed to load input file: {e}")
        return

    valid_df, excluded_ids = validate_elements(df)

    if len(excluded_ids) > 0:
        logger.warning(f"Validation excluded {len(excluded_ids)} rows.")
        # Save the excluded rows to a separate file for inspection
        excluded_df = df.iloc[excluded_ids]
        excluded_path = project_root / "data" / "processed" / "excluded_rows.csv"
        excluded_df.to_csv(excluded_path, index=False)
        logger.info(f"Excluded rows saved to {excluded_path}")
    else:
        logger.info("No rows excluded. All elements are valid and abundant.")

    # Save the validated dataframe back to the original location
    # Or save to a new 'validated' file? The task says "exclude... from the final dataset".
    # We will overwrite the processed features file with the valid rows.
    valid_df.to_csv(input_path, index=False)
    logger.info(f"Validated dataset saved to {input_path}")

if __name__ == "__main__":
    main()