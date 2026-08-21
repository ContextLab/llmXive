"""
Uncertainty Flagger Module (Task T013c)

Implements logic to flag entries using the default ±10°C uncertainty bound
and propagates this flag for downstream model weighting.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from data_ingestion_metadata import parse_uncertainty, extract_instrument_model

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DEFAULT_UNCERTAINTY_COVERAGE = 10.0  # ±10°C default bound

def load_metadata(metadata_path: Path) -> List[Dict[str, Any]]:
    """
    Load parsed instrumentation metadata from JSON.
    
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

def flag_default_uncertainty_entries(
    metadata_entries: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Analyze metadata entries and flag those using the default uncertainty bound.
    
    This function implements the core logic for T013c:
    1. Iterates through metadata entries.
    2. Parses the uncertainty string (e.g., "±10°C").
    3. If no explicit uncertainty is found or it matches the default, flags it.
    4. Records the source of the uncertainty (explicit vs. default).
    
    Args:
        metadata_entries: List of metadata dictionaries.
        
    Returns:
        Dictionary containing:
            - 'flags': List of entries with their uncertainty status.
            - 'summary': Statistics on flagged entries.
    """
    flags = []
    default_count = 0
    explicit_count = 0
    
    for entry in metadata_entries:
        entry_id = entry.get('entry_id', 'unknown')
        uncertainty_str = entry.get('uncertainty_raw', '')
        
        # Parse the uncertainty value
        parsed_value = parse_uncertainty(uncertainty_str)
        
        is_default = False
        uncertainty_source = "explicit"
        
        if parsed_value is None:
            # No valid uncertainty found in string -> apply default
            is_default = True
            uncertainty_source = "default_applied"
            final_value = DEFAULT_UNCERTAINTY_COVERAGE
            default_count += 1
        elif abs(parsed_value - DEFAULT_UNCERTAINTY_COVERAGE) < 1e-6:
            # Explicitly stated as the default value -> still flag as default usage
            # (Often implies standard protocol was followed)
            is_default = True
            uncertainty_source = "explicit_default"
            final_value = parsed_value
            default_count += 1
        else:
            # Non-default explicit value
            final_value = parsed_value
            explicit_count += 1
        
        flag_record = {
            "entry_id": entry_id,
            "uncertainty_value": final_value,
            "uncertainty_source": uncertainty_source,
            "is_default_bound": is_default,
            "original_string": uncertainty_str
        }
        flags.append(flag_record)
        
        if is_default:
            logger.debug(
                f"Entry {entry_id} flagged with default uncertainty "
                f"({DEFAULT_UNCERTAINTY_COVERAGE}°C). Source: {uncertainty_source}"
            )
    
    summary = {
        "total_entries": len(metadata_entries),
        "default_bound_count": default_count,
        "explicit_non_default_count": explicit_count,
        "default_threshold": DEFAULT_UNCERTAINTY_COVERAGE
    }
    
    logger.info(
        f"Uncertainty flagging complete. "
        f"Default bound applied to {default_count}/{len(metadata_entries)} entries."
    )
    
    return {
        "flags": flags,
        "summary": summary
    }

def save_flags(
    result: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Save the uncertainty flags and summary to a JSON file.
    
    Args:
        result: The dictionary returned by flag_default_uncertainty_entries.
        output_path: Path to write the JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Uncertainty flags saved to {output_path}")

def main() -> None:
    """
    Main entry point for the uncertainty flagger script.
    
    Reads from data/raw/metadata.json (produced by T013b)
    and writes to data/raw/uncertainty_flags.json.
    """
    # Define paths relative to project root
    # Assuming script runs from project root or code/
    base_path = Path(__file__).resolve().parent.parent
    metadata_path = base_path / "data" / "raw" / "metadata.json"
    output_path = base_path / "data" / "raw" / "uncertainty_flags.json"
    
    logger.info(f"Starting uncertainty flagging process.")
    logger.info(f"Input: {metadata_path}")
    logger.info(f"Output: {output_path}")
    
    try:
        # Load metadata
        metadata_entries = load_metadata(metadata_path)
        if not metadata_entries:
            logger.warning("Metadata file is empty. No flags generated.")
            # Still create an empty output to satisfy artifact requirement
            save_flags({"flags": [], "summary": {"total_entries": 0}}, output_path)
            return

        # Process and flag
        result = flag_default_uncertainty_entries(metadata_entries)
        
        # Save results
        save_flags(result, output_path)
        
        logger.info("Process completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Required input file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        raise

if __name__ == "__main__":
    main()
