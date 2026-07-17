"""
Periodic Table Loader Module.

Loads elemental properties from the raw data file with strict validation.
Ensures data integrity before downstream processing.
"""

import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

# Ensure consistent logging configuration if not already done
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_elemental_properties(
    file_path: Optional[Path] = None,
    required_elements: Optional[List[str]] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Load elemental properties from a CSV file with strict validation.

    Args:
        file_path: Path to the CSV file. Defaults to 'data/raw/elemental_properties.csv'.
        required_elements: Optional list of element symbols that MUST be present.
                           If provided and missing, raises a ValueError.

    Returns:
        A dictionary mapping element symbols to their properties:
        {
            "Mn": {"electronegativity": 1.55, "atomic_radii": 127, "valence_electrons": 7},
            ...
        }

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the file is empty, malformed, or missing required elements.
        KeyError: If expected columns are missing from the CSV.
    """
    if file_path is None:
        # Resolve relative to project root structure
        file_path = Path("data/raw/elemental_properties.csv")

    if not file_path.exists():
        raise FileNotFoundError(
            f"Elemental properties file not found at: {file_path}. "
            "Ensure T006 has been completed successfully."
        )

    logger.info(f"Loading elemental properties from {file_path}")

    data: Dict[str, Dict[str, Any]] = {}
    required_columns = {"element", "electronegativity", "atomic_radii", "valence_electrons"}

    try:
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            # Validate header
            if reader.fieldnames is None:
                raise ValueError("CSV file is empty or has no header row.")

            header_set = set(reader.fieldnames)
            missing_cols = required_columns - header_set
            if missing_cols:
                raise KeyError(
                    f"CSV file missing required columns: {missing_cols}. "
                    f"Expected columns: {required_columns}"
                )

            row_count = 0
            for row in reader:
                row_count += 1
                element = row["element"].strip().upper()

                if not element:
                    logger.warning("Skipping row with empty element symbol.")
                    continue

                # Strict type conversion
                try:
                    electronegativity = float(row["electronegativity"])
                    atomic_radii = float(row["atomic_radii"])
                    valence_electrons = int(float(row["valence_electrons"]))
                except ValueError as e:
                    raise ValueError(
                        f"Invalid numeric value in row for element '{element}': {e}"
                    )

                # Basic sanity checks (physics bounds)
                if electronegativity <= 0 or electronegativity > 4.5:
                    logger.warning(
                        f"Element {element} has electronegativity {electronegativity} "
                        "outside expected range (0-4.5). Proceeding with caution."
                    )

                if atomic_radii <= 0 or atomic_radii > 300:
                    logger.warning(
                        f"Element {element} has atomic radius {atomic_radii} "
                        "outside expected range (0-300 pm). Proceeding with caution."
                    )

                if valence_electrons < 0 or valence_electrons > 18:
                    logger.warning(
                        f"Element {element} has valence electrons {valence_electrons} "
                        "outside expected range (0-18). Proceeding with caution."
                    )

                data[element] = {
                    "electronegativity": electronegativity,
                    "atomic_radii": atomic_radii,
                    "valence_electrons": valence_electrons
                }

            if row_count == 0:
                raise ValueError("CSV file contains no data rows.")

    except csv.Error as e:
        raise ValueError(f"Error parsing CSV file: {e}")

    # Validate required elements if specified
    if required_elements:
        missing = set(required_elements) - set(data.keys())
        if missing:
            raise ValueError(
                f"Required elements are missing from the dataset: {missing}. "
                "Ensure the dataset includes all necessary elements for alloy composition."
            )

    logger.info(f"Successfully loaded {len(data)} elements.")
    return data


def get_element_property(
    element: str,
    property_name: str,
    properties: Dict[str, Dict[str, Any]]
) -> Any:
    """
    Retrieve a specific property for an element.

    Args:
        element: Element symbol (e.g., 'Mn').
        property_name: Name of the property (e.g., 'electronegativity').
        properties: The dictionary loaded from load_elemental_properties.

    Returns:
        The value of the property.

    Raises:
        KeyError: If the element or property is not found.
    """
    element = element.strip().upper()
    if element not in properties:
        raise KeyError(f"Element '{element}' not found in properties data.")
    if property_name not in properties[element]:
        raise KeyError(
            f"Property '{property_name}' not found for element '{element}'. "
            f"Available: {list(properties[element].keys())}"
        )
    return properties[element][property_name]


def main() -> None:
    """
    Main entry point for testing/CLI usage of the loader.
    Loads the file and prints a summary.
    """
    try:
        # Define expected elements from T006 spec
        expected_elements = [
            "Mn", "Co", "Fe", "Ga", "Al", "Ni", "Cu", "Sn", "In", "Ti", "V"
        ]

        data = load_elemental_properties(
            file_path=Path("data/raw/elemental_properties.csv"),
            required_elements=expected_elements
        )

        print(f"Loaded {len(data)} elements successfully.")
        print(f"Sample entry (Mn): {data.get('Mn', 'Not found')}")

    except (FileNotFoundError, ValueError, KeyError) as e:
        logger.error(f"Failed to load elemental properties: {e}")
        raise


if __name__ == "__main__":
    main()