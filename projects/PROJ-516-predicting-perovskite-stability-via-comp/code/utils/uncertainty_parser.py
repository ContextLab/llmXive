"""
Uncertainty Parser Module

Parses temperature_precision from source metadata.
Defaults to ±10°C if missing and logs a warning.
"""

import logging
import re
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

DEFAULT_TEMPERATURE_PRECISION = 10.0  # ±10°C default


def parse_temperature_precision(metadata: Dict[str, Any]) -> Tuple[float, bool]:
    """
    Parse the temperature_precision value from source metadata.

    Args:
        metadata: Dictionary containing source metadata, potentially including
                  'temperature_precision', 'tga_model', or similar fields.

    Returns:
        Tuple of (precision_value, is_default):
            - precision_value: The parsed float value (°C).
            - is_default: True if the default value was used due to missing data.

    Note:
        If 'temperature_precision' is missing or cannot be parsed,
        defaults to DEFAULT_TEMPERATURE_PRECISION and logs a warning.
    """
    if not isinstance(metadata, dict):
        logger.warning("Metadata provided to parse_temperature_precision is not a dictionary. Using default.")
        return DEFAULT_TEMPERATURE_PRECISION, True

    # Attempt to find the key directly
    precision_value = metadata.get("temperature_precision")

    if precision_value is not None:
        try:
            parsed_val = float(precision_value)
            if parsed_val <= 0:
                logger.warning(f"Invalid temperature_precision value ({parsed_val}) found in metadata. Using default.")
                return DEFAULT_TEMPERATURE_PRECISION, True
            return parsed_val, False
        except (ValueError, TypeError):
            logger.warning(f"Could not parse temperature_precision '{precision_value}' as float. Using default.")
            return DEFAULT_TEMPERATURE_PRECISION, True

    # If not found directly, try common variations or search within nested structures
    # e.g., metadata.get("instrument", {}).get("precision")
    # But per spec, we look for 'temperature_precision' primarily.
    # If missing, we default.

    logger.warning(
        f"temperature_precision missing from source metadata. "
        f"Defaulting to ±{DEFAULT_TEMPERATURE_PRECISION}°C."
    )
    return DEFAULT_TEMPERATURE_PRECISION, True


def extract_uncertainty_flags(metadata_list: list) -> Dict[str, Any]:
    """
    Process a list of metadata entries to extract uncertainty flags and values.

    Args:
        metadata_list: List of metadata dictionaries from source data.

    Returns:
        Dictionary containing:
            - 'flags': List of booleans indicating if default uncertainty was used.
            - 'values': List of parsed precision values.
            - 'missing_count': Count of entries where precision was missing.
    """
    flags = []
    values = []
    missing_count = 0

    for i, meta in enumerate(metadata_list):
        val, is_default = parse_temperature_precision(meta)
        values.append(val)
        flags.append(is_default)
        if is_default:
            missing_count += 1

    return {
        "flags": flags,
        "values": values,
        "missing_count": missing_count,
        "total_entries": len(metadata_list)
    }


def main():
    """
    Entry point for testing the uncertainty parser.
    Reads metadata from a JSON file (if provided) or runs a demo.
    """
    import json
    import sys
    from pathlib import Path

    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
        if not input_path.exists():
            print(f"Error: File {input_path} not found.")
            sys.exit(1)

        with open(input_path, 'r') as f:
            data = json.load(f)

        if isinstance(data, list):
            results = extract_uncertainty_flags(data)
        elif isinstance(data, dict):
            results = extract_uncertainty_flags([data])
        else:
            print("Error: Input JSON must be a list or a single object.")
            sys.exit(1)

        print(json.dumps(results, indent=2))
    else:
        # Demo mode
        print("Running demo of uncertainty parser...")
        demo_data = [
            {"temperature_precision": 5.0, "source": "NREL"},
            {"instrument": "TGA-Q500", "source": "MP"},  # Missing precision
            {"temperature_precision": "2.5", "source": "Literature"},
            {"temperature_precision": -1.0, "source": "Bad Data"}  # Invalid
        ]
        results = extract_uncertainty_flags(demo_data)
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()