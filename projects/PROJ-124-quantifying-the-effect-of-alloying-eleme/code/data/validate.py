"""
Validation logic for the data pipeline.

This module provides functions to validate ingested data, specifically
excluding rows with unknown elements and logging specific warnings.
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple, Optional

import pandas as pd

from config.elements import get_abundant_elements_set
from utils.logger import get_logger

logger = get_logger(__name__)


def validate_elements(
    df: pd.DataFrame,
    composition_col: str = "composition",
    allowed_elements: Optional[Set[str]] = None
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Validate that all elements in the composition column are known/allowed.

    This function parses the composition string for each row, checks if
    all constituent elements are in the allowed set, and returns a filtered
    DataFrame containing only valid rows. It also collects warnings for
    invalid rows.

    Args:
        df: The input DataFrame containing composition data.
        composition_col: The name of the column containing composition strings.
        allowed_elements: A set of allowed element symbols. If None, uses the
            set of abundant elements defined in config.elements.

    Returns:
        A tuple containing:
            - filtered_df: DataFrame with rows containing only known elements.
            - warnings: A list of dictionaries containing details about excluded rows
              (index, composition, missing_elements).

    Raises:
        ValueError: If the composition column is missing or contains non-string data.
    """
    if allowed_elements is None:
        allowed_elements = get_abundant_elements_set()

    if composition_col not in df.columns:
        raise ValueError(f"Composition column '{composition_col}' not found in DataFrame.")

    if not pd.api.types.is_string_dtype(df[composition_col]):
        # Try to convert, but if it fails, raise error
        try:
            df[composition_col] = df[composition_col].astype(str)
        except Exception as e:
            raise ValueError(f"Composition column '{composition_col}' contains non-string data that cannot be converted: {e}")

    valid_indices = []
    warnings = []

    # Helper to parse composition string into elements
    # Expected format: "Element1_xxx Element2_yyy ..." or similar
    # We need to extract element symbols (e.g., "Fe", "Ni", "Zr")
    # A robust way is to use regex to find all element symbols
    import re
    # Regex to match element symbols (1 or 2 letters, first capital)
    element_pattern = re.compile(r'([A-Z][a-z]?)')

    for idx, row in df.iterrows():
        composition_str = row[composition_col]
        if pd.isna(composition_str) or not isinstance(composition_str, str):
            warnings.append({
                "index": idx,
                "composition": str(composition_str),
                "missing_elements": ["NaN/Invalid String"],
                "reason": "Invalid or missing composition string"
            })
            continue

        # Extract elements from the string
        found_elements = element_pattern.findall(composition_str)
        
        if not found_elements:
            warnings.append({
                "index": idx,
                "composition": composition_str,
                "missing_elements": [],
                "reason": "No element symbols found in composition string"
            })
            continue

        # Check if all found elements are in the allowed set
        missing = [elem for elem in found_elements if elem not in allowed_elements]

        if missing:
            warnings.append({
                "index": idx,
                "composition": composition_str,
                "missing_elements": list(set(missing)),
                "reason": "Contains unknown elements"
            })
        else:
            valid_indices.append(idx)

    if warnings:
        logger.warning(f"Found {len(warnings)} rows with unknown or invalid elements.")
        for w in warnings[:10]:  # Log first 10 warnings
            logger.warning(f"  Row {w['index']}: Composition='{w['composition']}', Missing={w['missing_elements']}")
        if len(warnings) > 10:
            logger.warning(f"  ... and {len(warnings) - 10} more rows with unknown elements.")
    else:
        logger.info("All rows contain valid elements.")

    filtered_df = df.iloc[valid_indices].reset_index(drop=True)
    return filtered_df, warnings


def main():
    """
    Main entry point for validation script.
    Reads processed features, validates elements, and saves the filtered result.
    """
    config = get_environment_config()
    input_path = Path(config["data"]["processed"]["features_csv"])
    output_path = Path(config["data"]["processed"]["features_validated_csv"])

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)

    logger.info(f"Loaded {len(df)} rows. Validating elements...")
    valid_df, warnings = validate_elements(df)

    logger.info(f"Filtered data: {len(valid_df)} valid rows, {len(warnings)} excluded.")

    # Save validated data
    output_path.parent.mkdir(parents=True, exist_ok=True)
    valid_df.to_csv(output_path, index=False)
    logger.info(f"Saved validated data to {output_path}")

    # Save warnings log (optional, for debugging)
    warnings_path = Path(config["state"]["validation_warnings_json"])
    if warnings:
        import json
        warnings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(warnings_path, 'w') as f:
            json.dump(warnings, f, indent=2)
        logger.info(f"Saved validation warnings to {warnings_path}")

    return valid_df, warnings


if __name__ == "__main__":
    main()