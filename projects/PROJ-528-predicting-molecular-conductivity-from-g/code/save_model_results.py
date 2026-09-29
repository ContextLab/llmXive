import os
import json
import logging
import argparse
from typing import Dict, Any, List, Optional
from code.config import DATA_PATH
from code.logging_config import setup_logging

logger = logging.getLogger(__name__)

def get_default_results() -> Dict[str, Any]:
    """Return the default structure for model_results.json if it doesn't exist."""
    return {
        "rf_r2": 0.0,
        "gb_r2": 0.0,
        "cv_scores": [],
        "sensitivity_analysis": {},
        "vif_scores": []
    }

def initialize_results_file(filepath: str) -> None:
    """Initialize the results file with default values if it does not exist."""
    if not os.path.exists(filepath):
        logger.info(f"Initializing {filepath} with default structure.")
        with open(filepath, 'w') as f:
            json.dump(get_default_results(), f, indent=2)

def load_results(filepath: str) -> Dict[str, Any]:
    """Load results from the JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"Results file {filepath} not found. Returning defaults.")
        return get_default_results()
    
    with open(filepath, 'r') as f:
        return json.load(f)

def save_results_to_json(results: Dict[str, Any], filepath: str) -> None:
    """Save the results dictionary to a JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {filepath}")

def main():
    """
    Finalize model_results.json by updating it with final R²/MAE from T039c (VIF loop)
    and T032 (Sensitivity analysis).
    
    This script aggregates results from:
    1. data/processed/vif_iteration_log.json (Final VIF iteration metrics)
    2. data/processed/sensitivity_analysis.json (Sensitivity variance metrics)
    3. Updates data/processed/model_results.json
    """
    setup_logging()
    
    results_path = os.path.join(DATA_PATH, "processed", "model_results.json")
    vif_log_path = os.path.join(DATA_PATH, "processed", "vif_iteration_log.json")
    sensitivity_path = os.path.join(DATA_PATH, "processed", "sensitivity_analysis.json")
    
    # Load existing results or initialize
    results = load_results(results_path)
    
    # Update with VIF Loop Final Metrics (from T039c)
    if os.path.exists(vif_log_path):
        try:
            with open(vif_log_path, 'r') as f:
                vif_log = json.load(f)
            
            iterations = vif_log.get('iterations', [])
            if iterations:
                final_iteration = iterations[-1]
                results['rf_r2'] = final_iteration.get('r2', 0.0)
                # Assuming MAE is stored as 'mae' in the log
                results['mae'] = final_iteration.get('mae', 0.0) 
                results['vif_scores'] = final_iteration.get('vif_scores', {})
                logger.info(f"Updated results with final VIF iteration R2: {results['rf_r2']}")
            else:
                logger.warning("VIF log exists but has no iterations.")
        except Exception as e:
            logger.error(f"Failed to load VIF log: {e}")
    else:
        logger.warning(f"VIF log not found at {vif_log_path}. Skipping VIF update.")

    # Update with Sensitivity Analysis (from T032)
    if os.path.exists(sensitivity_path):
        try:
            with open(sensitivity_path, 'r') as f:
                sensitivity_data = json.load(f)
            
            results['sensitivity_analysis'] = {
                'thresholds': sensitivity_data.get('thresholds', []),
                'r2_variance': sensitivity_data.get('r2_variance', 0.0),
                'range': sensitivity_data.get('range', 0.0),
                'population_variance': sensitivity_data.get('population_variance', 0.0)
            }
            logger.info("Updated results with sensitivity analysis data.")
        except Exception as e:
            logger.error(f"Failed to load sensitivity analysis: {e}")
    else:
        logger.warning(f"Sensitivity analysis not found at {sensitivity_path}. Skipping sensitivity update.")

    # Save the finalized results
    save_results_to_json(results, results_path)
    
    logger.info("T033b Finalization complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Finalize model results JSON")
    parser.parse_args()
    main()
