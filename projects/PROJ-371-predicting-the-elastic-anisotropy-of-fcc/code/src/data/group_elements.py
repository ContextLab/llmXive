"""
Group elements module for LOEO cross-validation.

Parses chemical formulas from the cleaned dataset and generates
element-to-material-ID mappings required for Leave-One-Element-Out splitting.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import pandas as pd
import re

# Import config for paths
from src.utils.config import get_path, ensure_directories
from src.utils.logging import get_logger

# Re-use formula parsing logic from features.py to ensure consistency
# We import the function if it exists, or define a minimal version here
try:
    from src.data.features import parse_formula as features_parse_formula
except ImportError:
    features_parse_formula = None

logger = get_logger(__name__)


def load_cleaned_data(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the cleaned dataset from the processed directory.

    Args:
        input_path: Optional explicit path. If None, uses config default.

    Returns:
        DataFrame containing cleaned elastic data with 'formula' and 'material_id' columns.
    """
    if input_path is None:
        input_path = str(get_path("data_processed", "elastic_anisotropy.csv"))

    path_obj = Path(input_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Cleaned data file not found at {input_path}")

    logger.info(f"Loading cleaned data from {input_path}")
    df = pd.read_csv(input_path)

    required_cols = {"formula", "material_id"}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Cleaned data missing required columns: {missing}")

    # Ensure no nulls in key columns
    if df["formula"].isnull().any() or df["material_id"].isnull().any():
        logger.warning("Cleaned data contains null values in formula or material_id; dropping rows.")
        df = df.dropna(subset=["formula", "material_id"])

    return df


def parse_formula_simple(formula: str) -> Set[str]:
    """
    Parse a chemical formula string into a set of unique element symbols.
    Handles standard formula notation (e.g., "Fe2O3", "CuAl2").

    Args:
        formula: Chemical formula string.

    Returns:
        Set of unique element symbols found in the formula.
    """
    if not isinstance(formula, str):
        return set()

    # Regex to match element symbols: Capital letter followed by optional lowercase
    # This is a robust regex for standard chemical formulas
    elements = re.findall(r'([A-Z][a-z]?)', formula)
    return set(elements)


def build_element_groups(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Build a mapping of element -> list of material IDs.

    Iterates through the dataframe, parsing each formula to extract elements,
    and accumulating material IDs for each element.

    Args:
        df: DataFrame with 'formula' and 'material_id' columns.

    Returns:
        Dictionary mapping element symbol (str) to list of material IDs (str).
    """
    element_groups: Dict[str, Set[str]] = {}
    total_rows = len(df)

    for idx, row in df.iterrows():
        formula = row["formula"]
        material_id = row["material_id"]

        try:
            # Use the shared parser if available, otherwise fallback to simple regex
            if features_parse_formula:
                elements = features_parse_formula(formula)
            else:
                elements = parse_formula_simple(formula)

            if not elements:
                logger.debug(f"No elements found in formula: {formula} at row {idx}")
                continue

            for elem in elements:
                if elem not in element_groups:
                    element_groups[elem] = set()
                element_groups[elem].add(material_id)

        except Exception as e:
            logger.warning(f"Failed to parse formula '{formula}' at row {idx}: {e}")
            continue

    # Convert sets to sorted lists for deterministic JSON output
    return {k: sorted(list(v)) for k, v in element_groups.items()}


def save_element_groups(groups: Dict[str, List[str]], output_path: Optional[str] = None) -> str:
    """
    Save the element groups dictionary to a JSON file.

    Args:
        groups: The element-to-materials mapping.
        output_path: Optional explicit path. If None, uses config default.

    Returns:
        The path where the file was saved.
    """
    if output_path is None:
        output_path = str(get_path("data_processed", "element_groups.json"))

    path_obj = Path(output_path)
    ensure_directories(path_obj)

    logger.info(f"Saving element groups to {output_path}")
    with open(path_obj, 'w', encoding='utf-8') as f:
        json.dump(groups, f, indent=2)

    logger.info(f"Saved {len(groups)} unique elements to {output_path}")
    return output_path


def group_elements_pipeline(
    input_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> str:
    """
    Execute the full grouping pipeline: load, parse, build, save.

    Args:
        input_path: Path to cleaned CSV.
        output_path: Path for output JSON.

    Returns:
        Path to the generated JSON file.
    """
    logger.info("Starting element grouping pipeline")

    df = load_cleaned_data(input_path)
    logger.info(f"Loaded {len(df)} records")

    groups = build_element_groups(df)
    logger.info(f"Built groups for {len(groups)} unique elements")

    saved_path = save_element_groups(groups, output_path)

    logger.info("Element grouping pipeline completed successfully")
    return saved_path


def main() -> int:
    """
    CLI entry point for the group_elements module.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Running group_elements.py")

    try:
        # Use config defaults for paths unless overridden by CLI args (not implemented for simplicity here)
        output_path = group_elements_pipeline()
        logger.info(f"Pipeline finished. Output: {output_path}")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        return 1
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
