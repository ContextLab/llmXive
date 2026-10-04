"""
Finalize Sensitivity Analysis Results (Task T032c).
Updates data/processed/model_results.json with sensitivity analysis results.
"""
import os
import json
import logging
import argparse
from typing import Dict, Any, Optional

# Configure logging
from code.logging_config import setup_logging
logger = setup_logging()

# Import config
import code.config as config

# Import existing analysis functions if needed, though we mostly read files here
# We assume T032b has already run and produced sensitivity_analysis.json

RESULTS_PATH = os.path.join(config.DATA_PATH, "model_results.json")
SENSITIVITY_PATH = os.path.join(config.DATA_PATH, "sensitivity_analysis.json")

def load_results(path: str) -> Dict[str, Any]:
    """Load existing results or return defaults if file doesn't exist."""
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {
        "rf_r2": 0.0,
        "gb_r2": 0.0,
        "cv_scores": [],
        "sensitivity_analysis": {},
        "vif_scores": []
    }

def save_results(path: str, data: Dict[str, Any]) -> None:
    """Save results to JSON."""
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved results to {path}")

def main():
    """
    Main entry point for T032c.
    Reads sensitivity_analysis.json (produced by T032b) and merges it into model_results.json.
    """
    logger.info("Starting T032c: Finalize Sensitivity Results")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)

    # Load existing results
    results = load_results(RESULTS_PATH)
    logger.info(f"Loaded existing results from {RESULTS_PATH}")

    # Check if sensitivity analysis file exists
    if not os.path.exists(SENSITIVITY_PATH):
        logger.warning(f"Sensitivity analysis file not found at {SENSITIVITY_PATH}. "
                       "Skipping merge. Ensure T032b has completed successfully.")
        # Still save the current results (which might be empty/defaults)
        save_results(RESULTS_PATH, results)
        return

    # Load sensitivity analysis results
    with open(SENSITIVITY_PATH, 'r') as f:
        sensitivity_data = json.load(f)

    logger.info(f"Loaded sensitivity data from {SENSITIVITY_PATH}")
    logger.info(f"Sensitivity keys: {list(sensitivity_data.keys())}")

    # Merge sensitivity data into results
    # The schema expects 'sensitivity_analysis' to contain the data
    results['sensitivity_analysis'] = sensitivity_data

    # Optionally, extract final metrics from sensitivity if needed,
    # but T032c specifically says "Update ... with sensitivity analysis results"
    # so we store the full object.

    # Save updated results
    save_results(RESULTS_PATH, results)

    logger.info("T032c completed successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Finalize Sensitivity Results (T032c)")
    parser.parse_args()
    main()