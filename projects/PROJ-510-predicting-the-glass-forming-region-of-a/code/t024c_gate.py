"""
Gate task for SC-002: Check if model is statistically distinguishable from null.
Logs warning if not met, but does not fail the pipeline.
"""
import json
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/t024c_gate.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

STAT_COMPARISON_PATH = "data/models/statistical_comparison.json"
SC002_STATUS_PATH = "data/models/sc002_status.json"
MODELS_DIR = "data/models"

os.makedirs(MODELS_DIR, exist_ok=True)

def load_statistical_comparison():
    """Load statistical comparison results."""
    with open(STAT_COMPARISON_PATH, 'r') as f:
        return json.load(f)

def check_sc002_gate():
    """
    Check if SC-002 is met and log status.
    """
    logger.info("Checking SC-002 gate")

    result = load_statistical_comparison()
    sc002_met = result.get('sc002_met', False)

    status = "PASSED" if sc002_met else "FAILED"
    status_file = {
        "sc002_status": status,
        "p_value": result.get('p_value'),
        "t_statistic": result.get('t_statistic')
    }

    with open(SC002_STATUS_PATH, 'w') as f:
        json.dump(status_file, f, indent=2)

    if not sc002_met:
        logger.warning("SC-002 failed: Model not statistically distinguishable from null")
    else:
        logger.info("SC-002 passed: Model is statistically distinguishable from null")

    return status_file

def run_gate():
    """Main entry point."""
    check_sc002_gate()

def main():
    run_gate()

if __name__ == "__main__":
    main()
