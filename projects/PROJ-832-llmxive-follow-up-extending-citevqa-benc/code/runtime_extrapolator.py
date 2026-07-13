import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from config import get_config_dict

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def load_pilot_results(pilot_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Loads the pilot evaluation results.
    Expects a JSON file containing 'total_runtime_seconds' and 'num_samples_processed'.
    """
    config = get_config_dict()
    results_dir = Path(config['paths']['results'])
    
    if pilot_path is None:
        # Default path based on task description context
        pilot_path = str(results_dir / "pilot_evaluation_results.json")
    
    if not os.path.exists(pilot_path):
        raise FileNotFoundError(f"Pilot results not found at {pilot_path}. "
                                "Please run T018a (pilot evaluation) first.")
    
    with open(pilot_path, 'r') as f:
        return json.load(f)

def calculate_extrapolation(pilot_data: Dict[str, Any], total_test_size: int) -> Dict[str, Any]:
    """
    Extrapolates total runtime based on pilot data.
    
    Args:
        pilot_data: Dict containing 'total_runtime_seconds' and 'num_samples_processed'.
        total_test_size: The total number of samples in the held-out test set.
    
    Returns:
        Dict with extrapolation details and verification against SC-004 (6-hour limit).
    """
    pilot_runtime = pilot_data.get('total_runtime_seconds', 0)
    pilot_samples = pilot_data.get('num_samples_processed', 0)
    
    if pilot_samples == 0:
        raise ValueError("Pilot data indicates 0 samples processed; cannot extrapolate.")
    
    avg_time_per_sample = pilot_runtime / pilot_samples
    estimated_total_time_seconds = avg_time_per_sample * total_test_size
    estimated_total_time_hours = estimated_total_time_seconds / 3600.0
    
    # SC-004: 6-hour limit
    limit_hours = 6.0
    limit_seconds = limit_hours * 3600.0
    fits_within_limit = estimated_total_time_seconds <= limit_seconds
    
    return {
        "pilot_runtime_seconds": pilot_runtime,
        "pilot_samples": pilot_samples,
        "average_time_per_sample_seconds": avg_time_per_sample,
        "total_test_set_size": total_test_size,
        "estimated_total_runtime_seconds": estimated_total_time_seconds,
        "estimated_total_runtime_hours": estimated_total_time_hours,
        "limit_hours": limit_hours,
        "limit_seconds": limit_seconds,
        "fits_within_limit": fits_within_limit,
        "sc_004_status": "PASS" if fits_within_limit else "FAIL"
    }

def main():
    """
    Main entry point for T018b.
    1. Loads pilot results (from T018a).
    2. Defines total test set size (hardcoded based on CiteVQA standard split or config).
    3. Calculates extrapolation.
    4. Saves results to data/results/runtime_estimate.json.
    """
    config = get_config_dict()
    results_dir = Path(config['paths']['results'])
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine total test set size. 
    # In a real scenario, this might come from the dataset metadata or config.
    # For CiteVQA, we assume a standard split or read from a config value if available.
    # Defaulting to a reasonable placeholder if not in config, but ideally this is known.
    # Let's check config first.
    total_test_size = config.get('hyperparameters', {}).get('test_set_size', 1000)
    
    logger.info(f"Loading pilot results to extrapolate runtime for {total_test_size} samples.")
    
    try:
        pilot_data = load_pilot_results()
        logger.info(f"Pilot data loaded: {pilot_data['num_samples_processed']} samples in {pilot_data['total_runtime_seconds']}s")
        
        extrapolation_result = calculate_extrapolation(pilot_data, total_test_size)
        
        output_path = results_dir / "runtime_estimate.json"
        with open(output_path, 'w') as f:
            json.dump(extrapolation_result, f, indent=2)
        
        logger.info(f"Extrapolation complete. Saved to {output_path}")
        logger.info(f"Estimated runtime: {extrapolation_result['estimated_total_runtime_hours']:.2f} hours")
        logger.info(f"SC-004 Status: {extrapolation_result['sc_004_status']}")
        
        if not extrapolation_result['fits_within_limit']:
            logger.warning("WARNING: Estimated runtime exceeds the 6-hour limit defined in SC-004.")
            
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    except Exception as e:
        logger.error(f"Error during extrapolation: {e}")
        raise

if __name__ == "__main__":
    main()
