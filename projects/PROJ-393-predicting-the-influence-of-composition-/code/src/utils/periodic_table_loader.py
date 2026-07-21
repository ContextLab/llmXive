"""
Periodic Table Loader for Heusler Alloy Analysis.

Loads and validates elemental properties from the raw data CSV.
Provides strict validation and caching for efficient access.
"""
import csv
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from .logging_config import setup_logging

# Initialize logger
logger = logging.getLogger(__name__)

# Default path relative to project root
DEFAULT_DATA_PATH = Path("data/raw/elemental_properties.csv")

# Cache for loaded properties
_properties_cache: Optional[Dict[str, Dict[str, Any]]] = None
_cache_path: Optional[Path] = None

def _calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of the file for validation."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_elemental_properties(data_path: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    """
    Load elemental properties from CSV with strict validation.

    Args:
        data_path: Path to the elemental_properties.csv file.
                   Defaults to data/raw/elemental_properties.csv.

    Returns:
        Dictionary mapping element symbols to their properties.

    Raises:
        FileNotFoundError: If the data file does not exist.
        ValueError: If the data file is empty or missing required columns.
        KeyError: If an element has missing required properties.
    """
    global _properties_cache, _cache_path

    # Use default path if none provided
    if data_path is None:
        data_path = DEFAULT_DATA_PATH

    # Resolve to absolute path relative to project root
    if not data_path.is_absolute():
        # Assume project root is parent of 'code' directory
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        data_path = project_root / data_path

    # Check if file exists
    if not data_path.exists():
        raise FileNotFoundError(
            f"Elemental properties file not found at: {data_path}. "
            "Please ensure T006 has generated data/raw/elemental_properties.csv."
        )

    # Check cache validity
    if _properties_cache is not None and _cache_path == data_path:
        logger.debug(f"Using cached properties from {data_path}")
        return _properties_cache

    # Load and validate data
    logger.info(f"Loading elemental properties from {data_path}")
    properties = {}
    required_columns = {'element', 'electronegativity', 'atomic_radii', 'valence_electrons', 'source_reference'}

    try:
        with open(data_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            # Validate header
            if reader.fieldnames is None:
                raise ValueError("CSV file is empty or has no header.")

            header_set = set(reader.fieldnames)
            missing_cols = required_columns - header_set
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

            row_count = 0
            for row_num, row in enumerate(reader, start=2): # Start at 2 (header is 1)
                row_count += 1

                # Validate element symbol
                element = row['element'].strip()
                if not element:
                    raise ValueError(f"Row {row_num}: Empty element symbol.")

                # Validate numeric fields
                try:
                    electronegativity = float(row['electronegativity'])
                    atomic_radii = float(row['atomic_radii'])
                    valence_electrons = int(row['valence_electrons'])
                except ValueError as e:
                    raise ValueError(f"Row {row_num}: Invalid numeric value for element {element}: {e}")

                # Validate ranges (basic sanity checks)
                if not (0 < electronegativity < 5.0):
                    logger.warning(f"Row {row_num}: Electronegativity {electronegativity} for {element} seems unusual.")
                if not (50 < atomic_radii < 250): # Angstroms * 100 approx
                    logger.warning(f"Row {row_num}: Atomic radii {atomic_radii} for {element} seems unusual.")
                if not (1 <= valence_electrons <= 18):
                    logger.warning(f"Row {row_num}: Valence electrons {valence_electrons} for {element} seems unusual.")

                properties[element] = {
                    'electronegativity': electronegativity,
                    'atomic_radii': atomic_radii,
                    'valence_electrons': valence_electrons,
                    'source_reference': row['source_reference'].strip()
                }

            if row_count == 0:
                raise ValueError("CSV file contains no data rows.")

            logger.info(f"Loaded {row_count} elements from {data_path}")

            # Update cache
            _properties_cache = properties
            _cache_path = data_path

            return properties

    except csv.Error as e:
        raise ValueError(f"CSV parsing error: {e}")

def get_element_property(element: str, property_name: str, data_path: Optional[Path] = None) -> Any:
    """
    Get a specific property for an element.

    Args:
        element: Element symbol (e.g., 'Fe', 'Co').
        property_name: Name of the property (e.g., 'electronegativity', 'atomic_radii').
        data_path: Optional path to override default data file.

    Returns:
        The property value.

    Raises:
        KeyError: If element or property is not found.
        FileNotFoundError: If data file is missing.
    """
    properties = load_elemental_properties(data_path)

    if element not in properties:
        raise KeyError(f"Element '{element}' not found in periodic table data. "
                       f"Available elements: {list(properties.keys())}")

    if property_name not in properties[element]:
        raise KeyError(f"Property '{property_name}' not found for element '{element}'. "
                       f"Available properties: {list(properties[element].keys())}")

    return properties[element][property_name]

def get_all_elements(data_path: Optional[Path] = None) -> List[str]:
    """
    Get a list of all available element symbols.

    Args:
        data_path: Optional path to override default data file.

    Returns:
        List of element symbols.
    """
    properties = load_elemental_properties(data_path)
    return list(properties.keys())

def validate_elements_in_dataset(elements: List[str], data_path: Optional[Path] = None) -> Tuple[List[str], List[str]]:
    """
    Validate a list of elements against the loaded periodic table.

    Args:
        elements: List of element symbols to validate.
        data_path: Optional path to override default data file.

    Returns:
        Tuple of (valid_elements, invalid_elements).
    """
    available = set(get_all_elements(data_path))
    valid = []
    invalid = []

    for elem in elements:
        if elem in available:
            valid.append(elem)
        else:
            invalid.append(elem)

    return valid, invalid

def main():
    """
    Main entry point for command-line execution.
    Validates the data file and prints summary.
    """
    setup_logging(level=logging.INFO)
    logger.info("Running periodic table loader validation...")

    try:
        props = load_elemental_properties()
        logger.info(f"Successfully loaded {len(props)} elements.")
        logger.info(f"Elements: {', '.join(sorted(props.keys()))}")

        # Verify specific known elements for Heusler alloys
        expected = ['Mn', 'Co', 'Fe', 'Ga', 'Al', 'Ni', 'Cu', 'Sn']
        missing = [e for e in expected if e not in props]
        if missing:
            logger.warning(f"Missing expected Heusler elements: {missing}")
        else:
            logger.info("All expected Heusler elements present.")

        return 0

    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())