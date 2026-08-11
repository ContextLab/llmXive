"""
Uncertainty flagging module for perovskite stability analysis.

This module identifies entries where the TGA uncertainty was not explicitly
parsed and flags them as using the default ±10°C bound. These flags are
essential for downstream model weighting (1/σ).
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from data_ingestion_metadata import parse_uncertainty, extract_instrument_model

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants matching the project specification
DEFAULT_UNCERTAINTY_CELSIUS = 10.0
DEFAULT_FLAG_VALUE = "default_bound"
EXPLICIT_FLAG_VALUE = "explicit_bound"

def load_metadata(metadata_path: Path) -> List[Dict[str, Any]]:
    """
    Load the parsed metadata JSON file.

    Args:
        metadata_path: Path to the metadata JSON file.

    Returns:
        List of metadata entries.

    Raises:
        FileNotFoundError: If the metadata file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    with open(metadata_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def flag_default_uncertainty_entries(metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Identify entries that rely on the default uncertainty bound.

    This function iterates through the metadata entries. If an entry's
    uncertainty field is missing, None, or explicitly indicates a default
    value, it is flagged. Otherwise, it is marked as explicit.

    Args:
        metadata: List of metadata dictionaries containing 'uncertainty' info.

    Returns:
        List of entries with an added 'uncertainty_flag' field.
    """
    flagged_entries = []
    default_count = 0
    explicit_count = 0

    for entry in metadata:
        entry_copy = entry.copy()
        uncertainty_str = entry_copy.get('uncertainty')
        
        # Parse the uncertainty to check if it's a real value or missing
        parsed = parse_uncertainty(uncertainty_str)
        
        if parsed is None or parsed.get('value') is None:
            # No valid uncertainty found, must use default
            entry_copy['uncertainty_flag'] = DEFAULT_FLAG_VALUE
            entry_copy['T_d_uncertainty'] = DEFAULT_UNCERTAINTY_CELSIUS
            default_count += 1
        else:
            # Valid uncertainty found
            entry_copy['uncertainty_flag'] = EXPLICIT_FLAG_VALUE
            entry_copy['T_d_uncertainty'] = parsed.get('value')
            explicit_count += 1
        
        flagged_entries.append(entry_copy)

    logger.info(f"Flagging complete: {default_count} entries use default ±{DEFAULT_UNCERTAINTY_CELSIUS}°C, "
                f"{explicit_count} entries have explicit bounds.")
    
    return flagged_entries

def save_flags(flagged_entries: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the flagged entries to a JSON file.

    Args:
        flagged_entries: List of entries with uncertainty flags.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(flagged_entries, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Uncertainty flags saved to {output_path}")

def main() -> None:
    """
    Main entry point for the uncertainty flagging process.
    
    Reads from data/raw/metadata.json and writes to data/raw/uncertainty_flags.json.
    """
    base_dir = Path(__file__).resolve().parent.parent.parent
    metadata_path = base_dir / "data" / "raw" / "metadata.json"
    output_path = base_dir / "data" / "raw" / "uncertainty_flags.json"

    logger.info(f"Loading metadata from {metadata_path}")
    try:
        metadata = load_metadata(metadata_path)
    except FileNotFoundError as e:
        logger.error(f"Failed to load metadata: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in metadata file: {e}")
        raise

    logger.info("Flagging entries with default uncertainty bounds...")
    flagged_entries = flag_default_uncertainty_entries(metadata)

    logger.info(f"Saving results to {output_path}")
    save_flags(flagged_entries, output_path)

    logger.info("Uncertainty flagging process completed successfully.")

if __name__ == "__main__":
    main()
