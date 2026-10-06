import logging
import re
from typing import Any, Dict, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_PRECISION = 10.0  # ±10°C

def parse_temperature_precision(precision_str: Optional[str]) -> Tuple[float, bool]:
    """
    Parse a temperature precision string (e.g., "±5°C", "5", "5.0").
    
    Args:
        precision_str: The string to parse.
    
    Returns:
        A tuple of (precision_value, is_parsed_successfully).
        If parsing fails or input is None, returns (DEFAULT_PRECISION, False).
    """
    if precision_str is None:
        logger.warning("Precision string is None. Using default.")
        return DEFAULT_PRECISION, False

    if isinstance(precision_str, (int, float)):
        return float(precision_str), True

    # Clean string
    clean_str = str(precision_str).strip()
    if not clean_str:
        logger.warning("Precision string is empty. Using default.")
        return DEFAULT_PRECISION, False

    # Remove common symbols
    clean_str = re.sub(r'[±~]', '', clean_str)
    clean_str = re.sub(r'°?C$', '', clean_str)
    
    try:
        value = float(clean_str)
        if value < 0:
            logger.warning(f"Negative precision value {value} detected. Using absolute value.")
            value = abs(value)
        return value, True
    except ValueError:
        logger.warning(f"Could not parse precision string '{precision_str}'. Using default.")
        return DEFAULT_PRECISION, False

def extract_uncertainty_flags(metadata_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and parse uncertainty information from a metadata entry.
    
    Args:
        metadata_entry: Dictionary containing 'temperature_precision' and other fields.
    
    Returns:
        Updated dictionary with parsed 'precision_value' and 'precision_source'.
    """
    raw_precision = metadata_entry.get('temperature_precision')
    parsed_value, is_parsed = parse_temperature_precision(raw_precision)
    
    metadata_entry['precision_value'] = parsed_value
    metadata_entry['precision_source'] = 'source' if is_parsed else 'default'
    
    if not is_parsed:
        logger.warning(f"Missing precision for {metadata_entry.get('formula', 'Unknown')}, defaulting to {DEFAULT_PRECISION}°C")
    
    return metadata_entry

def main():
    """Test the uncertainty parser."""
    test_cases = [
        "±5°C",
        "10",
        "5.0",
        "±10",
        None,
        "",
        "invalid"
    ]
    
    for tc in test_cases:
        val, ok = parse_temperature_precision(tc)
        logger.info(f"Input: {tc} -> Value: {val}, Parsed: {ok}")

if __name__ == '__main__':
    main()