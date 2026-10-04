import os
import sys
import json
import logging
import argparse
from typing import List, Dict, Any

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from code.logging_config import setup_logging
from code.analysis import run_sensitivity_analysis
from code.config import DATA_PATH, SENSITIVITY_THRESHOLDS, SEED

logger = logging.getLogger(__name__)

def main():
    """
    Execute sensitivity analysis loop and save results.
    This script is the entry point for T032b (Sensitivity Analysis Loop)
    and T032c (Finalize Sensitivity).
    """
    setup_logging()
    logger.info("Starting sensitivity analysis pipeline.")

    # Ensure output directory exists
    os.makedirs(os.path.join(DATA_PATH, "processed"), exist_ok=True)

    try:
        # Run the sensitivity analysis which handles:
        # 1. Iterating over thresholds
        # 2. Filtering data
        # 3. Retraining models
        # 4. Saving intermediate models
        # 5. Saving sensitivity_analysis.json
        results = run_sensitivity_analysis()

        # T032c: Finalize Sensitivity
        # Update data/processed/model_results.json with sensitivity results
        model_results_path = os.path.join(DATA_PATH, "processed", "model_results.json")
        
        # Load existing results if they exist, otherwise start fresh
        if os.path.exists(model_results_path):
            with open(model_results_path, 'r') as f:
                final_results = json.load(f)
        else:
            final_results = {
                "rf_r2": 0.0,
                "gb_r2": 0.0,
                "cv_scores": [],
                "sensitivity_analysis": {},
                "vif_scores": [],
                "quantum_proxy_metadata": {}
            }

        # Merge sensitivity results
        if results:
            final_results["sensitivity_analysis"] = {
                "thresholds": results.get("thresholds", []),
                "r2_scores": results.get("r2_scores", []),
                "r2_variance": results.get("r2_variance", 0.0),
                "range": results.get("range", 0.0),
                "population_variance": results.get("population_variance", 0.0)
            }
            
            # Update best R2 if sensitivity analysis found better models
            if results.get("best_rf_r2"):
                final_results["rf_r2"] = results["best_rf_r2"]
            if results.get("best_gb_r2"):
                final_results["gb_r2"] = results["best_gb_r2"]

        # Write final results
        with open(model_results_path, 'w') as f:
            json.dump(final_results, f, indent=2)

        logger.info(f"Sensitivity analysis complete. Results saved to {model_results_path}")
        logger.info(f"Sensitivity thresholds tested: {results.get('thresholds', [])}")
        logger.info(f"R2 variance across thresholds: {results.get('r2_variance', 0.0)}")

        return 0

    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
