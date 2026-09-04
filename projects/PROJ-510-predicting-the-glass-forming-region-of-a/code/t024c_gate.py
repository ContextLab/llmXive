"""
Task T024c: SC-002 Statistical Significance Gate.

This script loads the statistical comparison results from T024a and
determines if the model is statistically distinguishable from the null model.
It logs a WARNING if the condition is not met but does NOT raise an exception,
allowing the pipeline to continue and report the negative finding.
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

# Paths
STAT_COMPARISON_PATH = "data/models/statistical_comparison.json"
STATUS_OUTPUT_PATH = "data/models/sc002_status.json"


def load_statistical_comparison(path: str) -> dict:
    """Load the statistical comparison JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Statistical comparison file not found at {path}. "
                                "Ensure T024a has run successfully.")
    
    with open(path, 'r') as f:
        return json.load(f)


def check_sc002_gate(comparison_data: dict) -> bool:
    """
    Check if the SC-002 condition is met (p_value < 0.05).
    
    Args:
        comparison_data: Dictionary containing 'p_value', 't_statistic', 'sc002_met'.
    
    Returns:
        True if sc002_met is True, False otherwise.
    """
    return comparison_data.get('sc002_met', False)


def run_gate():
    """
    Main execution logic for T024c.
    
    1. Load statistical_comparison.json.
    2. Check if sc002_met is True.
    3. Log WARNING if False, SUCCESS if True.
    4. Save status to sc002_status.json.
    """
    logger.info("Starting SC-002 Gate Check (T024c)...")
    
    try:
        # 1. Load data
        comparison_data = load_statistical_comparison(STAT_COMPARISON_PATH)
        logger.info(f"Loaded statistical comparison: {comparison_data}")
        
        # 2. Check condition
        is_met = check_sc002_gate(comparison_data)
        
        # 3. Log result and prepare status
        status = "PASSED"
        if not is_met:
            logger.warning("SC-002 failed: Model not statistically distinguishable from null.")
            logger.warning(f"P-value: {comparison_data.get('p_value')}, T-statistic: {comparison_data.get('t_statistic')}")
            status = "FAILED"
        else:
            logger.info("SC-002 PASSED: Model is statistically distinguishable from null.")
        
        # 4. Save status file
        status_data = {
            "sc002_status": status,
            "p_value": comparison_data.get('p_value'),
            "t_statistic": comparison_data.get('t_statistic'),
            "sc002_met": is_met
        }
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(STATUS_OUTPUT_PATH), exist_ok=True)
        
        with open(STATUS_OUTPUT_PATH, 'w') as f:
            json.dump(status_data, f, indent=2)
        
        logger.info(f"Gate check complete. Status saved to {STATUS_OUTPUT_PATH}")
        logger.info(f"Result: {status}")
        
    except FileNotFoundError as e:
        logger.error(f"Critical dependency missing: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in statistical comparison file: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during gate check: {e}")
        raise


def main():
    """Entry point for the script."""
    run_gate()


if __name__ == "__main__":
    main()
