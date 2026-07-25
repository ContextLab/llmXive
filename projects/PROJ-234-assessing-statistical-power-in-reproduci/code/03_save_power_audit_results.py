"""
Task T033: Save results to data/processed/power_audit_results.json.

Loads computed power and MDES results, validates them, and saves the final
audit results JSON file with the required schema:
{dataset_id, observed_power, mdes, threshold_met, status}.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from sibling modules as per API surface
from utils.logging_config import setup_logging

logger = logging.getLogger(__name__)

def load_power_results(input_path: Path) -> List[Dict[str, Any]]:
    """Load the power audit results computed by 03_compute_sensitivity.py."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected a list of results in {input_path}, got {type(data)}")
    
    logger.info(f"Loaded {len(data)} power audit results from {input_path}")
    return data

def process_and_save_results(
    results: List[Dict[str, Any]],
    output_path: Path,
    threshold: float = 0.8
) -> List[Dict[str, Any]]:
    """
    Process raw power results to match the T033 schema and save to JSON.
    
    The output schema must contain:
    - dataset_id: int
    - observed_power: float (clamped to [0, 1])
    - mdes: float
    - threshold_met: bool (observed_power >= threshold)
    - status: str ("success" or "failed")
    """
    processed_results = []
    
    for item in results:
        dataset_id = item.get('dataset_id')
        observed_power = item.get('observed_power')
        mdes = item.get('mdes')
        
        if dataset_id is None:
            logger.warning(f"Skipping result missing dataset_id: {item}")
            continue
        
        if observed_power is None or mdes is None:
            logger.warning(f"Skipping result missing power or MDES for dataset {dataset_id}: {item}")
            continue
        
        # Clamp observed_power to [0, 1] as per spec
        observed_power = max(0.0, min(1.0, float(observed_power)))
        mdes = float(mdes)
        
        # Determine threshold_met and status
        threshold_met = observed_power >= threshold
        status = "success" if threshold_met else "failed"
        
        processed_item = {
            "dataset_id": dataset_id,
            "observed_power": observed_power,
            "mdes": mdes,
            "threshold_met": threshold_met,
            "status": status
        }
        
        processed_results.append(processed_item)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(processed_results, f, indent=2)
    
    logger.info(f"Saved {len(processed_results)} processed results to {output_path}")
    
    # Log summary statistics
    success_count = sum(1 for r in processed_results if r['status'] == 'success')
    failure_count = len(processed_results) - success_count
    logger.info(f"Summary: {success_count} passed threshold, {failure_count} failed")
    
    return processed_results

def main():
    """Main entry point for T033."""
    # Setup logging
    log_config = setup_logging()
    
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    input_file = project_root / 'data' / 'processed' / 'power_audit_results_raw.json'
    output_file = project_root / 'data' / 'processed' / 'power_audit_results.json'
    
    logger.info(f"Starting T033: Saving power audit results")
    logger.info(f"Input: {input_file}")
    logger.info(f"Output: {output_file}")
    
    try:
        # Load raw results
        results = load_power_results(input_file)
        
        # Process and save
        process_and_save_results(results, output_file)
        
        logger.info("T033 completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error processing results: {e}")
        raise

if __name__ == '__main__':
    main()
