import os
import json
import logging
from typing import Dict, Any, Optional

from utils.constants import get_vif_threshold
from utils.logger import get_logger, log_pipeline_step

logger = get_logger(__name__)

def write_vif_results_to_json(
    vif_results: Dict[str, Any],
    output_path: str
) -> None:
    """
    Write VIF results, threshold, and comparison status to a JSON file.
    This function creates the initial model_results.json file if it doesn't exist,
    or updates the 'vif_results' key if it does.

    Args:
        vif_results: Dictionary containing threshold, vif_values, and overall_status
                     (output from check_vif_results)
        output_path: Path to the output JSON file (e.g., 'data/processed/model_results.json')
    """
    log_pipeline_step("Writing VIF results to JSON")
    logger.info(f"Writing VIF results to {output_path}")

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Load existing data if file exists
    existing_data = {}
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r') as f:
                existing_data = json.load(f)
            logger.info(f"Loaded existing data from {output_path}")
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not read existing file, starting fresh: {e}")
            existing_data = {}

    # Update or add vif_results
    existing_data['vif_results'] = vif_results

    # Write back to file
    with open(output_path, 'w') as f:
        json.dump(existing_data, f, indent=2)

    logger.info("Successfully wrote VIF results to JSON")

def main():
    """
    Main entry point for the VIF writer module.
    """
    logger.info("VIF Writer module loaded")
    print("Use write_vif_results_to_json() to write results.")

if __name__ == "__main__":
    main()