"""
Task T024c: Statistical Significance Gate (SC-002)

This script acts as a gate for the pipeline. It loads the results of the
statistical comparison (T024a) and verifies that the model is statistically
distinguishable from the null model.

If the p-value is >= 0.05 (sc002_met is false), it raises a ValueError
to halt the pipeline, as the model has not demonstrated statistical
significance over a dummy baseline.
"""
import json
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Path constants
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAT_COMPARISON_PATH = os.path.join(
    PROJECT_ROOT, "data", "models", "statistical_comparison.json"
)

def load_statistical_comparison():
    """Load the statistical comparison results from JSON."""
    if not os.path.exists(STAT_COMPARISON_PATH):
        raise FileNotFoundError(
            f"Statistical comparison file not found at {STAT_COMPARISON_PATH}. "
            "Ensure T024a (statistical_test.py) has been run successfully."
        )
    
    with open(STAT_COMPARISON_PATH, 'r') as f:
        return json.load(f)

def check_sc002_gate(results: dict) -> bool:
    """
    Check if the SC-002 requirement is met.
    
    Args:
        results: Dictionary containing 'sc002_met', 'p_value', 't_statistic'.
        
    Returns:
        True if the gate passes, False otherwise.
        
    Raises:
        ValueError: If the gate fails (model not statistically distinguishable).
    """
    sc002_met = results.get('sc002_met', False)
    p_value = results.get('p_value', 1.0)
    t_statistic = results.get('t_statistic', 0.0)
    
    logger.info(f"Loaded statistical test results: p_value={p_value:.6f}, t_statistic={t_statistic:.6f}")
    
    if not sc002_met:
        error_msg = (
            f"SC-002 failed: Model is not statistically distinguishable from null. "
            f"p_value ({p_value:.6f}) >= 0.05. "
            "The model does not significantly outperform the dummy baseline."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("SC-002 PASSED: Model is statistically distinguishable from null (p < 0.05).")
    return True

def run_gate():
    """Main entry point for the gate task."""
    try:
        logger.info("Starting SC-002 Statistical Significance Gate check...")
        results = load_statistical_comparison()
        check_sc002_gate(results)
        logger.info("Gate check successful. Proceeding with pipeline.")
        return 0
    except FileNotFoundError as e:
        logger.critical(f"Missing required data file: {e}")
        return 1
    except ValueError as e:
        logger.critical(f"Gate failed: {e}")
        return 1
    except Exception as e:
        logger.critical(f"Unexpected error during gate check: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run_gate())