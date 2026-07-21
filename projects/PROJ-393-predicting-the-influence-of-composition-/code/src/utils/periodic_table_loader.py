"""
Periodic Table Loader Module

Loads and validates elemental properties from the raw data CSV.
Provides strict validation and lookup utilities for the pipeline.
"""

import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import logging setup from sibling module
from .logging_config import setup_logging

# Constants
REQUIRED_COLUMNS = ['element', 'electronegativity', 'atomic_radii', 'valence_electrons']
DEFAULT_FILE_PATH = "data/raw/elemental_properties.csv"

# Global cache for loaded properties
_properties_cache: Optional[Dict[str, Dict[str, Any]]] = None
_logger: Optional[logging.Logger] = None

def _get_logger() -> logging.Logger:
    """Get or create the module logger."""
    global _logger
    if _logger is None:
        _logger = setup_logging(__name__)
    return _logger

def load_elemental_properties(file_path: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    Load elemental properties from the CSV file with strict validation.

    Args:
        file_path: Path to the CSV file. Defaults to DEFAULT_FILE_PATH.

    Returns:
        Dictionary mapping element symbols to their properties.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the file is missing required columns or has invalid data.
    """
    global _properties_cache
    logger = _get_logger()

    if file_path is None:
        # Resolve relative to project root (code/)
        base_dir = Path(__file__).resolve().parent.parent.parent
        file_path = str(base_dir / DEFAULT_FILE_PATH)

    path_obj = Path(file_path)

    if not path_obj.exists():
        logger.error(f"Elemental properties file not found: {file_path}")
        raise FileNotFoundError(f"Elemental properties file not found: {file_path}")

    # Check cache first
    if _properties_cache is not None:
        logger.debug("Loading elemental properties from cache")
        return _properties_cache

    logger.info(f"Loading elemental properties from {file_path}")
    properties = {}

    try:
        with open(path_obj, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # Validate headers
            if reader.fieldnames is None:
                raise ValueError("CSV file is empty or has no header row")

            missing_cols = set(REQUIRED_COLUMNS) - set(reader.fieldnames)
            if missing_cols:
                raise ValueError(f"Missing required columns in {file_path}: {missing_cols}")

            row_count = 0
            for row in reader:
                row_count += 1
                element = row['element'].strip()
                if not element:
                    logger.warning(f"Skipping row {row_count}: Empty element symbol")
                    continue

                # Validate and parse numeric fields
                try:
                    electronegativity = float(row['electronegativity'])
                    atomic_radii = float(row['atomic_radii'])
                    valence_electrons = float(row['valence_electrons'])
                except ValueError as e:
                    logger.error(f"Invalid numeric data in row {row_count} for element {element}: {e}")
                    raise ValueError(f"Invalid numeric data for element {element}: {e}")

                # Basic sanity checks
                if electronegativity < 0:
                    raise ValueError(f"Negative electronegativity for {element}: {electronegativity}")
                if atomic_radii <= 0:
                    raise ValueError(f"Non-positive atomic radii for {element}: {atomic_radii}")
                if valence_electrons < 0:
                    raise ValueError(f"Negative valence electrons for {element}: {valence_electrons}")

                properties[element] = {
                    'electronegativity': electronegativity,
                    'atomic_radii': atomic_radii,
                    'valence_electrons': valence_electrons
                }

            if row_count == 0:
                logger.warning(f"No data rows found in {file_path}")

        logger.info(f"Successfully loaded {len(properties)} elemental properties")
        _properties_cache = properties
        return properties

    except csv.Error as e:
        logger.error(f"CSV parsing error in {file_path}: {e}")
        raise

def get_element_property(element: str, property_name: str, file_path: Optional[str] = None) -> Optional[float]:
    """
    Get a specific property for an element.

    Args:
        element: Element symbol (e.g., 'Fe', 'Co').
        property_name: Name of the property to retrieve.
        file_path: Optional path to override default file location.

    Returns:
        The property value if found, None otherwise.

    Raises:
        ValueError: If the property name is invalid.
    """
    valid_properties = {'electronegativity', 'atomic_radii', 'valence_electrons'}
    if property_name not in valid_properties:
        raise ValueError(f"Invalid property name '{property_name}'. Must be one of {valid_properties}")

    properties = load_elemental_properties(file_path)
    element_upper = element.strip().upper()

    if element_upper not in properties:
        _get_logger().warning(f"Element '{element}' not found in periodic table data.")
        return None

    return properties[element_upper][property_name]

def main() -> None:
    """
    Main entry point for command-line execution.
    Loads the file and prints a summary.
    """
    logger = setup_logging(__name__, level=logging.INFO)
    logger.info("Running periodic_table_loader main function")

    try:
        props = load_elemental_properties()
        logger.info(f"Loaded {len(props)} elements:")
        for elem, data in sorted(props.items()):
            logger.info(f"  {elem}: EN={data['electronegativity']}, R={data['atomic_radii']}, VE={data['valence_electrons']}")
    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise

if __name__ == "__main__":
    main()
