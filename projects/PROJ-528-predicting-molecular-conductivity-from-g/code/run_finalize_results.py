"""
Finalize model results by updating data/processed/model_results.json with
final R²/MAE from the VIF loop and sensitivity analysis.

This script implements task T033b.
"""
import os
import sys
import json
import logging
import argparse

# Add project root to path if needed (for local execution)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.logging_config import setup_logging
from code.config import DATA_PATH

# Setup logging
logger = setup_logging()

RESULTS_FILE = os.path.join(DATA_PATH, 'processed', 'model_results.json')
SENSITIVITY_FILE = os.path.join(DATA_PATH, 'processed', 'sensitivity_analysis.json')
VIF_LOG_FILE = os.path.join(DATA_PATH, 'processed', 'vif_iteration_log.json')

def load_json(path):
    """Load JSON file, return empty dict if not found."""
    if not os.path.exists(path):
        logger.warning(f"File not found: {path}. Returning empty dict.")
        return {}
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading {path}: {e}")
        return {}

def save_json(path, data):
    """Save data to JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved results to {path}")

def finalize_results():
    """
    Update data/processed/model_results.json with final R²/MAE from:
    - T039d (VIF loop): The last iteration's R² and MAE.
    - T032c (Sensitivity): The variance and scores from sensitivity analysis.
    """
    logger.info("Starting finalization of model results (T033b)...")

    # Load existing results (or create default structure if T033a ran but no data)
    results = load_json(RESULTS_FILE)
    if not results:
        results = {
            "rf_r2": 0.0,
            "gb_r2": 0.0,
            "cv_scores": [],
            "sensitivity_analysis": {},
            "vif_scores": [],
            "final_vif_r2": None,
            "final_vif_mae": None,
            "sensitivity_variance": None
        }

    # Load Sensitivity Analysis Results (T032c)
    sensitivity_data = load_json(SENSITIVITY_FILE)
    if sensitivity_data:
        logger.info("Incorporating sensitivity analysis results.")
        results['sensitivity_analysis'] = sensitivity_data
        if 'r2_variance' in sensitivity_data:
            results['sensitivity_variance'] = sensitivity_data['r2_variance']
        if 'thresholds' in sensitivity_data:
            results['sensitivity_analysis']['thresholds'] = sensitivity_data['thresholds']
        if 'r2_scores' in sensitivity_data:
            results['sensitivity_analysis']['r2_scores'] = sensitivity_data['r2_scores']
    else:
        logger.warning("Sensitivity analysis file not found. Skipping sensitivity update.")

    # Load VIF Iteration Log (T039c/d)
    vif_log = load_json(VIF_LOG_FILE)
    if vif_log and 'iterations' in vif_log and len(vif_log['iterations']) > 0:
        logger.info("Incorporating VIF loop results.")
        # Get the last iteration
        last_iter = vif_log['iterations'][-1]
        final_r2 = last_iter.get('r2')
        final_mae = last_iter.get('mae')

        if final_r2 is not None:
            results['final_vif_r2'] = final_r2
            # Also update generic rf_r2/gb_r2 if we assume RF is the primary model
            # or keep them separate. Per spec, we update the specific fields.
            results['rf_r2'] = final_r2 

        if final_mae is not None:
            results['final_vif_mae'] = final_mae

        # Store full VIF scores history if available
        if 'vif_scores' in last_iter:
            results['vif_scores'] = last_iter['vif_scores']
    else:
        logger.warning("VIF iteration log not found or empty. Skipping VIF update.")

    # Save the finalized results
    save_json(RESULTS_FILE, results)
    logger.info("Finalization complete.")
    return results

def main():
    parser = argparse.ArgumentParser(description="Finalize model results (T033b)")
    parser.parse_args()
    finalize_results()

if __name__ == "__main__":
    main()