"""
T054: Edge Case - Collinearity Resolution Failure Handler

This script handles the edge case where the collinearity resolution process (T029b)
fails to identify a stable model after 3 drops (i.e., all features are collinear).

It logs a WARNING and saves the failure state to data/models/collinearity_resolution_failed.json.
It does NOT raise a ValueError, allowing the pipeline to continue with the best available model.
"""
import os
import sys
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)

from utils import get_logger, ensure_dir

# Configuration
MAX_DROPS = 3
COLLINEARITY_DECISION_FILE = "data/models/collinearity_decision.json"
COLLINEARITY_RESOLUTION_FAILED_FILE = "data/models/collinearity_resolution_failed.json"
BEST_AVAILABLE_MODEL_FILE = "data/models/random_forest_model_best_available.pkl"
STABLE_MODEL_FILE = "data/models/random_forest_model_stable.pkl"

def load_collinearity_decision() -> Optional[Dict[str, Any]]:
    """Load the collinearity decision file if it exists."""
    if not os.path.exists(COLLINEARITY_DECISION_FILE):
        return None
    with open(COLLINEARITY_DECISION_FILE, 'r') as f:
        return json.load(f)

def check_resolution_status(decision: Dict[str, Any]) -> bool:
    """
    Check if collinearity resolution has failed.
    
    Returns True if:
    - iterations >= MAX_DROPS
    - status is 'best_available' (meaning no stable subset was found)
    - retrain_required is True but no stable model was produced
    """
    if not decision:
        return False
    
    iterations = decision.get('iterations', 0)
    status = decision.get('status', '')
    retrain_required = decision.get('retrain_required', False)
    
    # Failure condition: max drops reached and still best_available
    if iterations >= MAX_DROPS and status == 'best_available':
        return True
    
    # Also check if we tried to retrain but ended up with best_available
    if retrain_required and status == 'best_available' and iterations >= 1:
        return True
        
    return False

def save_failure_state():
    """Save the collinearity resolution failure state to JSON."""
    ensure_dir(COLLINEARITY_RESOLUTION_FAILED_FILE)
    
    failure_record = {
        "status": "failed",
        "timestamp": datetime.now().isoformat(),
        "reason": "Collinearity resolution failed: No stable feature subset found after maximum iterations.",
        "max_drops_allowed": MAX_DROPS,
        "action_taken": "Proceeding with best available model.",
        "recommendation": "Review feature engineering to reduce collinearity or accept reduced model stability."
    }
    
    with open(COLLINEARITY_RESOLUTION_FAILED_FILE, 'w') as f:
        json.dump(failure_record, f, indent=2)
    
    logging.warning(f"Saved collinearity resolution failure state to {COLLINEARITY_RESOLUTION_FAILED_FILE}")

def verify_best_available_model_exists() -> bool:
    """Verify that a best available model exists as a fallback."""
    return os.path.exists(BEST_AVAILABLE_MODEL_FILE) or os.path.exists(STABLE_MODEL_FILE)

def run_collinearity_failure_handler():
    """
    Main entry point for T054.
    
    Checks if collinearity resolution has failed and handles it appropriately.
    """
    logger = get_logger(__name__)
    logger.info("Starting T054: Collinearity Resolution Failure Handler")
    
    # Load collinearity decision
    decision = load_collinearity_decision()
    
    if not decision:
        logger.info("No collinearity decision file found. Resolution may not have been attempted.")
        # Check if we have a best available model already
        if verify_best_available_model_exists():
            logger.info("Best available model exists. No failure state needed.")
            return
        else:
            logger.warning("No collinearity decision and no best available model found.")
            return
    
    # Check if resolution failed
    if check_resolution_status(decision):
        logger.warning("Collinearity resolution failed: No stable feature subset found. Proceeding with best available model.")
        
        # Verify we have a fallback model
        if not verify_best_available_model_exists():
            logger.error("CRITICAL: Collinearity resolution failed but no best available model exists!")
            # Still save the failure state for audit purposes
            save_failure_state()
            return
        
        # Save the failure state
        save_failure_state()
    else:
        logger.info("Collinearity resolution was successful or not applicable.")

def main():
    """Main function for script execution."""
    run_collinearity_failure_handler()

if __name__ == "__main__":
    main()
