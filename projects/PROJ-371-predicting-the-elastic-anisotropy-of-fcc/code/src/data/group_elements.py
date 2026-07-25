"""
Group elements by material ID for Leave-One-Element-Out (LOEO) cross-validation.

This module parses chemical formulas from the cleaned dataset and generates
a mapping of element -> list of material IDs. This mapping is required for
implementing LOEO cross-validation to prevent chemical similarity leakage.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

import pandas as pd

# Import from project utils
from src.utils.config import get_path, ensure_directories
from src.utils.logging import get_logger

# Import formula parsing from features module
from src.data.features import parse_formula


def load_cleaned_data(input_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the cleaned elastic data from the processed CSV file.

    Args:
        input_path: Path to the cleaned data CSV. If None, uses default path from config.

    Returns:
        DataFrame containing cleaned elastic data with 'material_id' and 'formula' columns.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing.
    """
    if input_path is None:
        input_path = get_path("processed_elastic_data")

    if not input_path.exists():
        raise FileNotFoundError(f"Cleaned data file not found: {input_path}")

    df = pd.read_csv(input_path)

    required_columns = {'material_id', 'formula'}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"Cleaned data missing required columns: {missing_columns}")

    return df


def build_element_groups(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Parse chemical formulas and build a mapping of element -> list of material IDs.

    Args:
        df: DataFrame with 'material_id' and 'formula' columns.

    Returns:
        Dictionary mapping each element symbol to a list of material IDs containing that element.
    """
    element_groups: Dict[str, Set[str]] = {}

    for _, row in df.iterrows():
        material_id = str(row['material_id'])
        formula = str(row['formula'])

        # Parse formula to get unique elements
        elements = parse_formula(formula)

        for element in elements:
            if element not in element_groups:
                element_groups[element] = set()
            element_groups[element].add(material_id)

    # Convert sets to sorted lists for JSON serialization
    return {elem: sorted(list(material_ids)) for elem, material_ids in element_groups.items()}


def save_element_groups(element_groups: Dict[str, List[str]], output_path: Optional[Path] = None) -> None:
    """
    Save the element groups mapping to a JSON file.

    Args:
        element_groups: Dictionary mapping elements to material ID lists.
        output_path: Path for the output JSON file. If None, uses default path from config.
    """
    if output_path is None:
        output_path = get_path("element_groups")

    ensure_directories([output_path])

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(element_groups, f, indent=2)

    logging.info(f"Element groups saved to {output_path}")


def group_elements_pipeline(input_path: Optional[Path] = None,
                             output_path: Optional[Path] = None) -> Dict[str, List[str]]:
    """
    Run the complete element grouping pipeline: load data, build groups, save results.

    Args:
        input_path: Path to cleaned data CSV. Defaults to config path.
        output_path: Path for output JSON. Defaults to config path.

    Returns:
        The element groups dictionary.
    """
    logger = get_logger(__name__)
    logger.info("Starting element grouping pipeline")

    # Load cleaned data
    df = load_cleaned_data(input_path)
    logger.info(f"Loaded {len(df)} records from {input_path}")

    # Build element groups
    element_groups = build_element_groups(df)
    logger.info(f"Found {len(element_groups)} unique elements across {len(df)} materials")

    # Save results
    save_element_groups(element_groups, output_path)

    logger.info("Element grouping pipeline completed successfully")
    return element_groups


def main() -> int:
    """
    Main entry point for the element grouping script.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # Use default paths from config
        input_path = get_path("processed_elastic_data")
        output_path = get_path("element_groups")

        element_groups = group_elements_pipeline(input_path, output_path)

        # Print summary
        print(f"\nElement Groups Summary:")
        print(f"  Total unique elements: {len(element_groups)}")
        print(f"  Output file: {output_path}")

        # Show some statistics
        element_counts = {elem: len(ids) for elem, ids in element_groups.items()}
        sorted_elements = sorted(element_counts.items(), key=lambda x: x[1], reverse=True)

        print(f"\nTop 10 most common elements:")
        for elem, count in sorted_elements[:10]:
            print(f"  {elem}: {count} materials")

        return 0

    except FileNotFoundError as e:
        logging.error(f"Input file not found: {e}")
        return 1
    except ValueError as e:
        logging.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error during element grouping: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
