"""
T023: Token Reduction Consistency Check.

Calculates the standard deviation of token savings from the per-trajectory
savings file. Checks if the standard deviation is less than 10% of the mean.
Writes the result to data/processed/token_consistency_report.json.

Depends on: T022a (token_savings_per_trajectory.csv)
"""

import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

INPUT_FILE = Path("data/processed/token_savings_per_trajectory.csv")
OUTPUT_FILE = Path("data/processed/token_consistency_report.json")

def check_consistency():
    """
    Reads token savings, calculates std_dev and mean, and checks the consistency condition.
    """
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}. "
            "Ensure T022a has been executed successfully."
        )

    logger.info(f"Loading data from {INPUT_FILE}")
    try:
        df = pd.read_csv(INPUT_FILE)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        raise

    if 'savings' not in df.columns:
        raise ValueError(f"Column 'savings' not found in {INPUT_FILE}")

    savings = df['savings'].dropna()

    if len(savings) == 0:
        logger.warning("No valid savings data found (all NaN or empty).")
        result = {
            "passed": False,
            "reason": "No valid savings data found.",
            "mean_savings": None,
            "std_dev_savings": None,
            "threshold": 0.10,
            "count": 0
        }
        write_output(result)
        return

    mean_savings = savings.mean()
    std_dev_savings = savings.std()

    logger.info(f"Mean savings: {mean_savings:.4f}")
    logger.info(f"Std Dev savings: {std_dev_savings:.4f}")

    # Condition: std_dev < 0.10 * mean_savings
    # Handle edge case where mean is 0 or negative (though savings should be positive)
    threshold_value = 0.10 * mean_savings
    
    if std_dev_savings is None or std_dev_savings != std_dev_savings: # Check for NaN
        passed = False
        reason = "Standard deviation is NaN or undefined."
    elif mean_savings == 0:
        # If mean is 0, any non-zero std dev fails. If std is 0, it passes.
        passed = (std_dev_savings == 0)
        reason = "Mean savings is 0. Passed only if std_dev is 0."
    else:
        passed = std_dev_savings < threshold_value
        reason = "Consistency check passed" if passed else "Consistency check failed: high variance in savings."

    logger.info(f"Threshold (10% of mean): {threshold_value:.4f}")
    logger.info(f"Result: {'PASSED' if passed else 'FAILED'}")

    result = {
        "passed": passed,
        "mean_savings": float(mean_savings),
        "std_dev_savings": float(std_dev_savings),
        "threshold_multiplier": 0.10,
        "threshold_value": float(threshold_value),
        "count": int(len(savings)),
        "reason": reason
    }

    write_output(result)

def write_output(result: Dict[str, Any]):
    """Writes the result dictionary to the output JSON file."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Writing report to {OUTPUT_FILE}")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info("Report written successfully.")

def main():
    """Main entry point."""
    try:
        check_consistency()
    except Exception as e:
        logger.critical(f"Token consistency check failed: {e}")
        raise

if __name__ == "__main__":
    main()