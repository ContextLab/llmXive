"""
Aggregate PR Scaling Results (Task T013b)

Reads `data/processed/scaling_fits.json`, verifies all W values are present,
and aggregates into a single list for downstream tasks (e.g., T015 Bonferroni).

This script acts as a validation and aggregation step to ensure the output
of T013a is complete and valid before statistical correction.
"""
import json
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Set

# Add project root to path to allow imports if run as script
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SCALING_FITS_PATH = PROJECT_ROOT / "data" / "processed" / "scaling_fits.json"
AGGREGATED_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "scaling_fits_aggregated.json"

def load_scaling_fits(path: Path) -> List[Dict[str, Any]]:
    """Load scaling fits from JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Scaling fits file not found: {path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected scaling_fits.json to be a list, got {type(data)}")
    
    return data

def verify_completeness(data: List[Dict[str, Any]], expected_widths: List[float]) -> bool:
    """Verify all expected disorder widths are present in the data."""
    present_widths: Set[float] = set()
    for entry in data:
        if 'disorder_width' in entry:
            present_widths.add(float(entry['disorder_width']))
    
    missing_widths = set(expected_widths) - present_widths
    if missing_widths:
        logger.error(f"Missing disorder widths in scaling_fits.json: {missing_widths}")
        return False
    
    logger.info(f"Verified all expected disorder widths are present: {present_widths}")
    return True

def validate_schema(data: List[Dict[str, Any]]) -> bool:
    """Validate that each entry has required keys."""
    required_keys = {'disorder_width', 'xi', 'uncertainty', 'p_value'}
    
    for i, entry in enumerate(data):
        if not isinstance(entry, dict):
            logger.error(f"Entry {i} is not a dictionary: {type(entry)}")
            return False
        
        missing_keys = required_keys - set(entry.keys())
        if missing_keys:
            logger.error(f"Entry {i} missing required keys: {missing_keys}")
            return False
        
        # Validate types
        try:
            float(entry['disorder_width'])
            float(entry['xi'])
            float(entry['uncertainty'])
            float(entry['p_value'])
        except (ValueError, TypeError) as e:
            logger.error(f"Entry {i} has invalid numeric values: {e}")
            return False
    
    logger.info("Schema validation passed for all entries")
    return True

def aggregate_results(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregate results into a single list structure.
    
    Currently, the input is already a list, but this function ensures
    a consistent output format and can be extended for future aggregation logic.
    """
    # Sort by disorder width for consistent ordering
    sorted_data = sorted(data, key=lambda x: float(x['disorder_width']))
    return sorted_data

def main():
    """Main entry point for T013b."""
    logger.info("Starting PR Scaling Results Aggregation (T013b)")
    
    # Load configuration to get expected W values
    try:
        config = get_config()
        expected_widths = config.get('W_LIST', [])
        if not expected_widths:
            logger.warning("No W_LIST found in config. Proceeding with validation only.")
            expected_widths = []
    except Exception as e:
        logger.warning(f"Could not load config for W_LIST: {e}. Proceeding with validation only.")
        expected_widths = []
    
    # Load scaling fits
    try:
        data = load_scaling_fits(SCALING_FITS_PATH)
        logger.info(f"Loaded {len(data)} entries from {SCALING_FITS_PATH}")
    except FileNotFoundError as e:
        logger.error(f"Failed to load scaling fits: {e}")
        logger.error("T013a must be run successfully before T013b can proceed.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in scaling_fits.json: {e}")
        sys.exit(1)
    
    # Verify completeness
    if expected_widths:
        is_complete = verify_completeness(data, expected_widths)
        if not is_complete:
            logger.error("Scaling fits are incomplete. Aborting.")
            sys.exit(1)
    
    # Validate schema
    if not validate_schema(data):
        logger.error("Schema validation failed. Aborting.")
        sys.exit(1)
    
    # Aggregate results
    aggregated = aggregate_results(data)
    
    # Write aggregated output
    AGGREGATED_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(AGGREGATED_OUTPUT_PATH, 'w') as f:
        json.dump(aggregated, f, indent=2)
    
    logger.info(f"Successfully aggregated {len(aggregated)} results to {AGGREGATED_OUTPUT_PATH}")
    logger.info("T013b completed successfully")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())