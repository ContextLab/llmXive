"""
T024c: Gate task for SC-002 (Statistical Significance).

This script loads the statistical comparison results from T024a.
It checks if the model is statistically distinguishable from the null model.
It logs a WARNING if the test fails but does NOT raise an exception,
allowing the pipeline to continue to report generation with this negative finding.

Output:
    data/models/sc002_status.json: Contains the status of the SC-002 check.
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
STATISTICAL_COMPARISON_PATH = "data/models/statistical_comparison.json"
OUTPUT_STATUS_PATH = "data/models/sc002_status.json"

def load_statistical_comparison(filepath: str) -> dict:
    """Load the statistical comparison results."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Statistical comparison file not found at {filepath}. "
                              "Ensure T024a has been executed successfully.")
    
    with open(filepath, 'r') as f:
        return json.load(f)

def check_sc002_gate(comparison_data: dict) -> bool:
    """
    Check if the SC-002 condition is met.
    
    Args:
        comparison_data: Dictionary containing 'p_value', 't_statistic', and 'sc002_met'.
    
    Returns:
        True if sc002_met is True, False otherwise.
    """
    return comparison_data.get('sc002_met', False)

def run_gate():
    """
    Main execution logic for the T024c gate task.
    
    1. Load statistical comparison results.
    2. Evaluate SC-002 status.
    3. Log WARNING if failed, SUCCESS if passed.
    4. Save status flag to sc002_status.json.
    """
    logger.info("Starting T024c Gate Task: SC-002 Statistical Significance Check")

    try:
        # Load comparison data
        logger.info(f"Loading statistical comparison from {STATISTICAL_COMPARISON_PATH}")
        comparison_data = load_statistical_comparison(STATISTICAL_COMPARISON_PATH)
        
        p_value = comparison_data.get('p_value', 0.0)
        t_statistic = comparison_data.get('t_statistic', 0.0)
        is_met = comparison_data.get('sc002_met', False)

        logger.info(f"Statistical Test Results: p-value={p_value:.4f}, t-statistic={t_statistic:.4f}")
        logger.info(f"SC-002 Met Status: {is_met}")

        # Determine status
        if not is_met:
            logger.warning("SC-002 failed: Model not statistically distinguishable from null.")
            status = "FAILED"
        else:
            logger.info("SC-002 passed: Model is statistically distinguishable from null.")
            status = "PASSED"

        # Prepare output
        status_data = {
            "sc002_status": status,
            "p_value": p_value,
            "t_statistic": t_statistic,
            "sc002_met": is_met,
            "message": "SC-002 check completed. Pipeline continues regardless of result."
        }

        # Ensure output directory exists
        os.makedirs(os.path.dirname(OUTPUT_STATUS_PATH), exist_ok=True)

        # Save status
        with open(OUTPUT_STATUS_PATH, 'w') as f:
            json.dump(status_data, f, indent=2)

        logger.info(f"Gate check complete. Status saved to {OUTPUT_STATUS_PATH}")
        logger.info(f"Final Status: {status}")

    except FileNotFoundError as e:
        logger.error(f"Critical Error: {e}")
        logger.error("Cannot proceed with gate check. Ensure T024a (statistical_test.py) has run successfully.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during gate check: {e}")
        sys.exit(1)

def main():
    """Entry point for the script."""
    run_gate()

if __name__ == "__main__":
    main()