import os
import json
import logging
from pathlib import Path
from typing import Dict, Any
from utils import setup_logging, log_info, log_warning, log_error, get_timestamp

# Configure logging for this module
logger = logging.getLogger(__name__)

def load_exclusion_counts(exclusion_counts_path: Path) -> Dict[str, Any]:
    """
    Load exclusion counts from the JSON file produced by T012a, T012b, and T012e.
    
    Args:
        exclusion_counts_path: Path to exclusion_counts.json
        
    Returns:
        Dictionary containing exclusion counts.
    """
    if not exclusion_counts_path.exists():
        log_error(f"Exclusion counts file not found: {exclusion_counts_path}")
        return {}
    
    try:
        with open(exclusion_counts_path, 'r') as f:
            data = json.load(f)
        log_info(f"Loaded exclusion counts from {exclusion_counts_path}")
        return data
    except json.JSONDecodeError as e:
        log_error(f"Failed to parse exclusion counts JSON: {e}")
        return {}
    except Exception as e:
        log_error(f"Unexpected error loading exclusion counts: {e}")
        return {}

def check_simulation_fallback(metadata_path: Path) -> bool:
    """
    Check if the pipeline ran in simulation mode by reading metadata.json.
    
    Args:
        metadata_path: Path to data/raw/metadata.json
        
    Returns:
        True if simulation_mode is True, False otherwise.
    """
    if not metadata_path.exists():
        log_warning(f"Metadata file not found: {metadata_path}. Assuming no simulation fallback.")
        return False
    
    try:
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        simulation_mode = metadata.get('simulation_mode', False)
        if simulation_mode:
            log_info("Simulation fallback detected in metadata.")
        return simulation_mode
    except Exception as e:
        log_error(f"Failed to read metadata for simulation check: {e}")
        return False

def generate_exclusion_log(
    exclusion_counts: Dict[str, Any],
    simulation_fallback: bool,
    output_path: Path
) -> Dict[str, Any]:
    """
    Generate the final exclusion log by aggregating counts and flags.
    
    Args:
        exclusion_counts: Dictionary with counts from previous steps.
        simulation_fallback: Boolean indicating if simulation fallback was used.
        output_path: Path to write the exclusion_log.json file.
        
    Returns:
        The generated exclusion log dictionary.
    """
    # Ensure all required keys exist, defaulting to 0 if missing
    log_data = {
        "ERR_MISSING_AGE_FIELD": exclusion_counts.get("ERR_MISSING_AGE_FIELD", 0),
        "ERR_MISSING_SCORE": exclusion_counts.get("ERR_MISSING_SCORE", 0),
        "ERR_MMSE_IMPAIRED": exclusion_counts.get("ERR_MMSE_IMPAIRED", 0),
        "SIMULATION_FALLBACK": simulation_fallback,
        "timestamp": get_timestamp()
    }
    
    # Calculate total exclusions
    total_exclusions = (
        log_data["ERR_MISSING_AGE_FIELD"] +
        log_data["ERR_MISSING_SCORE"] +
        log_data["ERR_MMSE_IMPAIRED"]
    )
    log_data["total_exclusions"] = total_exclusions
    
    # Log summary
    log_info(f"Generated exclusion log: {log_data}")
    
    # Write to file
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(log_data, f, indent=2)
        log_info(f"Successfully wrote exclusion log to {output_path}")
    except Exception as e:
        log_error(f"Failed to write exclusion log: {e}")
        raise
    
    return log_data

def main():
    """
    Main entry point for T012c: Generate Exclusion Log.
    
    Execution Order: T012a -> T012b -> T012e -> T012c
    """
    # Setup logging
    setup_logging()
    log_info("Starting T012c: Generate Exclusion Log")
    
    # Define paths relative to project root
    # Assuming execution from project root or code directory
    project_root = Path(__file__).resolve().parent.parent
    exclusion_counts_path = project_root / "data" / "processed" / "exclusion_counts.json"
    metadata_path = project_root / "data" / "raw" / "metadata.json"
    output_path = project_root / "data" / "processed" / "exclusion_log.json"
    
    # 1. Load exclusion counts (from T012a, T012b, T012e)
    exclusion_counts = load_exclusion_counts(exclusion_counts_path)
    if not exclusion_counts:
        log_error("No exclusion counts found. Cannot generate log.")
        return 1
    
    # 2. Check for simulation fallback (from T010a/T010b via metadata)
    simulation_fallback = check_simulation_fallback(metadata_path)
    
    # 3. Generate and save the exclusion log
    try:
        generate_exclusion_log(exclusion_counts, simulation_fallback, output_path)
        log_info("T012c completed successfully.")
        return 0
    except Exception as e:
        log_error(f"T012c failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())