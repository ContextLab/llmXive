"""
T013c: Implement logic to flag entries using the default ±10°C uncertainty bound.

This module reads the parsed instrumentation metadata from `data/raw/metadata.json`,
identifies entries where the uncertainty was not explicitly extracted (defaulting
to the project standard of ±10°C), and writes a flagging report to
`data/raw/uncertainty_flags.json`. It ensures this flag is propagated for
downstream model weighting (Task T020).
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

# Constants
DEFAULT_UNCERTAINTY = 10.0  # °C
DEFAULT_FLAG_KEY = "uses_default_uncertainty"
UNCERTAINTY_KEY = "T_d_uncertainty"
METADATA_PATH = Path("data/raw/metadata.json")
FLAG_OUTPUT_PATH = Path("data/raw/uncertainty_flags.json")

def load_metadata() -> List[Dict[str, Any]]:
    """Load parsed metadata from the JSON file generated in T013b."""
    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            f"Metadata file not found at {METADATA_PATH}. "
            "Please ensure T013b (data_ingestion_metadata.py) has been executed."
        )
    
    with open(METADATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Ensure we have a list of entries
    if isinstance(data, dict) and "entries" in data:
        return data["entries"]
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"Unexpected metadata format in {METADATA_PATH}")

def flag_default_uncertainty_entries(metadata_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Iterate through metadata entries and flag those using the default ±10°C uncertainty.
    
    Logic:
    1. Check if 'uncertainty' key exists in the entry.
    2. If missing or None, assign DEFAULT_UNCERTAINTY (10.0) and set the flag.
    3. If present, verify it's a number; if not, fallback to default and flag.
    4. Construct the output structure including the flag and the effective uncertainty.
    """
    flagged_entries = []
    default_count = 0
    explicit_count = 0

    for entry in metadata_entries:
        # Extract the raw uncertainty value if present
        raw_uncertainty = entry.get(UNCERTAINTY_KEY)
        
        is_default = False
        effective_uncertainty = None

        if raw_uncertainty is None:
            # No uncertainty found, apply default
            effective_uncertainty = DEFAULT_UNCERTAINTY
            is_default = True
        elif isinstance(raw_uncertainty, (int, float)):
            # Valid explicit uncertainty
            effective_uncertainty = float(raw_uncertainty)
            is_default = (effective_uncertainty == DEFAULT_UNCERTAINTY)
            # Note: If the explicit value happens to be exactly 10.0, 
            # we still treat it as explicit unless we have a source flag.
            # However, for safety in weighting, we only flag as 'default' 
            # if it was missing or unparseable. 
            # Re-reading task: "flag entries using the default ... bound".
            # Usually implies missing data. We will flag only if it was missing.
            is_default = False 
        else:
            # Invalid type, fallback to default
            effective_uncertainty = DEFAULT_UNCERTAINTY
            is_default = True

        if is_default:
            default_count += 1
            entry["T_d_uncertainty"] = effective_uncertainty
            entry[DEFAULT_FLAG_KEY] = True
        else:
            explicit_count += 1
            entry["T_d_uncertainty"] = effective_uncertainty
            entry[DEFAULT_FLAG_KEY] = False

        flagged_entries.append(entry)

    logger.info(f"Processed {len(metadata_entries)} entries: {default_count} default, {explicit_count} explicit.")

    return {
        "flagged_entries": flagged_entries,
        "summary": {
            "total_entries": len(metadata_entries),
            "default_uncertainty_count": default_count,
            "explicit_uncertainty_count": explicit_count,
            "default_bound_value": DEFAULT_UNCERTAINTY
        }
    }

def save_flags(result: Dict[str, Any]) -> None:
    """Save the flagging results to the output JSON file."""
    FLAG_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(FLAG_OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    logger.info(f"Saved uncertainty flags to {FLAG_OUTPUT_PATH}")

def main() -> None:
    """Main entry point for T013c."""
    logger.info("Starting T013c: Uncertainty Flagging")
    
    try:
        entries = load_metadata()
        result = flag_default_uncertainty_entries(entries)
        save_flags(result)
        
        # Log summary for verification
        summary = result["summary"]
        logger.info(f"Summary: {summary['default_uncertainty_count']} entries using default ±{summary['default_bound_value']}°C.")
        logger.info("T013c completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse metadata JSON: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during uncertainty flagging: {e}")
        raise

if __name__ == "__main__":
    main()
