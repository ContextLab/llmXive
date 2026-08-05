"""
Group elements by material ID for LOEO cross-validation.

This module parses chemical formulas from the cleaned dataset to generate
a mapping of elements to the material IDs they appear in. This mapping is
required for Leave-One-Element-Out (LOEO) cross-validation splitting.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import pandas as pd
import re

from src.utils.logging import get_logger, log_info, log_warning, log_error
from src.utils.config import get_path

logger = get_logger(__name__)

# Constants
FORMULA_PATTERN = re.compile(r'([A-Z][a-z]?)(\d*)')

def load_cleaned_data(data_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the cleaned and feature-engineered dataset.

    Args:
        data_path: Optional path to the CSV file. If None, uses config default.

    Returns:
        DataFrame containing the cleaned material data.

    Raises:
        FileNotFoundError: If the data file does not exist.
        ValueError: If the file is empty or missing required columns.
    """
    if data_path is None:
        data_path = str(get_path("data_processed", "elastic_anisotropy.csv"))

    path_obj = Path(data_path)
    if not path_obj.exists():
        log_error(f"Cleaned data file not found: {data_path}")
        raise FileNotFoundError(f"Cleaned data file not found: {data_path}")

    df = pd.read_csv(data_path)

    if df.empty:
        log_error("Cleaned data file is empty.")
        raise ValueError("Cleaned data file is empty.")

    required_cols = ["material_id", "formula"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        log_error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")

    log_info(f"Loaded {len(df)} rows from {data_path}")
    return df

def parse_formula_simple(formula: str) -> List[str]:
    """
    Parse a chemical formula string into a list of unique element symbols.

    Args:
        formula: Chemical formula string (e.g., "Fe2O3", "Al").

    Returns:
        List of unique element symbols found in the formula.
    """
    if not formula or not isinstance(formula, str):
        return []

    # Match element symbols: Capital letter optionally followed by lowercase
    # Ignore stoichiometric numbers
    matches = FORMULA_PATTERN.findall(formula)
    elements = [element for element, count in matches]

    # Return unique elements preserving order of first appearance
    seen = set()
    unique_elements = []
    for el in elements:
        if el not in seen:
            seen.add(el)
            unique_elements.append(el)

    return unique_elements

def build_element_groups(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Build a mapping from element symbols to lists of material IDs.

    Args:
        df: DataFrame containing 'material_id' and 'formula' columns.

    Returns:
        Dictionary mapping element symbols to lists of material IDs.
    """
    element_groups: Dict[str, Set[str]] = {}

    for _, row in df.iterrows():
        material_id = row["material_id"]
        formula = row["formula"]

        elements = parse_formula_simple(formula)

        for element in elements:
            if element not in element_groups:
                element_groups[element] = set()
            element_groups[element].add(material_id)

    # Convert sets to sorted lists for JSON serialization
    return {elem: sorted(list(ids)) for elem, ids in element_groups.items()}

def save_element_groups(groups: Dict[str, List[str]], output_path: Optional[str] = None) -> None:
    """
    Save element groups to a JSON file.

    Args:
        groups: Dictionary of element -> list of material IDs.
        output_path: Optional path for output file. If None, uses config default.
    """
    if output_path is None:
        output_path = str(get_path("data_processed", "element_groups.json"))

    path_obj = Path(output_path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)

    with open(path_obj, 'w', encoding='utf-8') as f:
        json.dump(groups, f, indent=2)

    log_info(f"Saved element groups to {output_path} ({len(groups)} unique elements)")

def group_elements_pipeline(input_path: Optional[str] = None, output_path: Optional[str] = None) -> Dict[str, List[str]]:
    """
    Run the full element grouping pipeline.

    Args:
        input_path: Path to cleaned data CSV.
        output_path: Path for output JSON.

    Returns:
        The generated element groups dictionary.
    """
    log_info("Starting element grouping pipeline")

    df = load_cleaned_data(input_path)
    groups = build_element_groups(df)
    save_element_groups(groups, output_path)

    log_info("Element grouping pipeline completed successfully")
    return groups

def main() -> None:
    """
    CLI entry point for element grouping.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate element groups for LOEO cross-validation."
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to cleaned data CSV (default: config path)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path for output JSON (default: config path)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    try:
        group_elements_pipeline(args.input, args.output)
    except Exception as e:
        log_error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
