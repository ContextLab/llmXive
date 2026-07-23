import logging
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple, Optional
import pandas as pd
from config.elements import get_abundant_elements_set
from utils.logger import get_logger

logger = get_logger(__name__)

def validate_elements(df: pd.DataFrame, composition_col: str = "composition") -> Tuple[pd.DataFrame, List[str]]:
    """
    Validates that all elements in the composition strings are known (in the abundant set).
    Excludes rows with unknown elements and logs specific warnings.

    Args:
        df: Input DataFrame containing composition data.
        composition_col: Name of the column containing composition strings (e.g., "Fe50Ni40B10").

    Returns:
        Tuple of (filtered_df, list_of_excluded_compositions).
    """
    known_elements = get_abundant_elements_set()
    excluded_rows = []
    excluded_compositions = []

    def parse_elements(comp_str: str) -> Set[str]:
        """
        Parses a composition string (e.g., "Fe50Ni40B10") into a set of element symbols.
        Handles standard chemical formula notation where element symbols start with uppercase
        and may be followed by lowercase letters, then optionally numbers.
        """
        import re
        # Regex to match element symbols: Uppercase followed by optional lowercase
        elements = re.findall(r'[A-Z][a-z]*', comp_str)
        return set(elements)

    valid_indices = []
    for idx, row in df.iterrows():
        comp_str = str(row[composition_col])
        elements_in_row = parse_elements(comp_str)
        
        unknown_elements = elements_in_row - known_elements
        
        if unknown_elements:
            excluded_compositions.append(comp_str)
            excluded_rows.append(idx)
            logger.warning(
                f"Row {idx}: Excluding composition '{comp_str}' due to unknown elements: {unknown_elements}"
            )
        else:
            valid_indices.append(idx)

    if excluded_rows:
        logger.warning(f"Total {len(excluded_rows)} rows excluded due to unknown elements.")
        filtered_df = df.iloc[valid_indices].reset_index(drop=True)
    else:
        logger.info("All rows contain only known elements.")
        filtered_df = df.copy()

    return filtered_df, excluded_compositions

def main():
    """
    Main entry point to run validation on the processed features dataset.
    Reads from data/processed/features.csv, filters unknown elements,
    and saves the result to data/processed/features_validated.csv.
    """
    input_path = Path("data/processed/features.csv")
    output_path = Path("data/processed/features_validated.csv")

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return

    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)

    if "composition" not in df.columns:
        logger.error("Input file must contain a 'composition' column.")
        return

    logger.info("Validating elements...")
    filtered_df, excluded = validate_elements(df, "composition")

    logger.info(f"Saving validated data to {output_path}")
    filtered_df.to_csv(output_path, index=False)

    logger.info(f"Validation complete. {len(excluded)} compositions excluded.")
    if excluded:
        logger.info(f"Excluded compositions: {excluded[:5]}...") # Log first 5

if __name__ == "__main__":
    main()