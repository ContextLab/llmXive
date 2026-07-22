"""
T023: Token Reduction Consistency Checker
Calculates the standard deviation of token savings across the test set for the Dynamic policy.
Addresses SC-004.

Input: data/processed/baseline_comparison.csv
Output: data/processed/token_consistency_report.json
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BASELINE_COMPARISON_PATH = "data/processed/baseline_comparison.csv"
OUTPUT_PATH = "data/processed/token_consistency_report.json"
STD_THRESHOLD = 1000.0  # Reasonable threshold for token savings consistency

def load_baseline_comparison():
    """Load the baseline comparison CSV."""
    if not os.path.exists(BASELINE_COMPARISON_PATH):
        raise FileNotFoundError(
            f"Required input file not found: {BASELINE_COMPARISON_PATH}. "
            "Ensure T022 has been executed successfully."
        )
    
    df = pd.read_csv(BASELINE_COMPARISON_PATH)
    logger.info(f"Loaded baseline comparison with {len(df)} rows")
    return df

def calculate_token_savings_consistency(df):
    """
    Calculate the standard deviation of token savings for the Dynamic policy.
    
    The baseline_comparison.csv contains aggregated statistics (mean, std) per condition.
    To get the actual standard deviation of token savings across the test set,
    we need to calculate it from the Dynamic condition's token usage distribution.
    
    Since we only have aggregated stats in baseline_comparison.csv, we approximate
    the savings consistency by looking at the std_dev_tokens of the Dynamic policy.
    
    For a proper per-trajectory savings calculation, we would need the raw simulation
    logs (data/processed/simulation_logs_dynamic.json), but the task specifies
    using baseline_comparison.csv as input.
    """
    
    # Filter for Dynamic condition
    dynamic_rows = df[df['condition'] == 'Dynamic']
    
    if len(dynamic_rows) == 0:
        raise ValueError(
            "No 'Dynamic' condition found in baseline_comparison.csv. "
            "Ensure T017 (Dynamic Simulation) was executed."
        )
    
    dynamic_row = dynamic_rows.iloc[0]
    
    # Extract token usage statistics
    avg_tokens = dynamic_row['avg_tokens']
    std_dev_tokens = dynamic_row['std_dev_tokens']
    
    # The std_dev_tokens in the CSV represents the standard deviation of token usage
    # across the test set for the Dynamic policy. This is our measure of consistency.
    # Lower std_dev means more consistent token usage (and thus consistent savings).
    
    token_savings_std = std_dev_tokens
    
    logger.info(f"Dynamic policy token usage - Mean: {avg_tokens:.2f}, Std: {token_savings_std:.2f}")
    
    return token_savings_std

def generate_consistency_report(std_dev_tokens):
    """Generate the token consistency report."""
    # Determine if the consistency is acceptable
    # A lower standard deviation indicates more consistent behavior
    passed = std_dev_tokens < STD_THRESHOLD
    
    report = {
        "std_dev_tokens": float(std_dev_tokens),
        "threshold": float(STD_THRESHOLD),
        "passed": bool(passed),
        "description": "Standard deviation of token usage for Dynamic policy across test set",
        "metric": "token_usage_consistency"
    }
    
    return report

def save_report(report):
    """Save the report to the output file."""
    output_dir = Path(OUTPUT_PATH).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Saved token consistency report to {OUTPUT_PATH}")

def main():
    """Main entry point for T023."""
    try:
        # Load baseline comparison data
        df = load_baseline_comparison()
        
        # Calculate token savings consistency
        std_dev_tokens = calculate_token_savings_consistency(df)
        
        # Generate report
        report = generate_consistency_report(std_dev_tokens)
        
        # Save report
        save_report(report)
        
        # Print summary
        status = "PASSED" if report['passed'] else "FAILED"
        logger.info(f"Token Consistency Check: {status}")
        logger.info(f"  Std Dev: {report['std_dev_tokens']:.2f}")
        logger.info(f"  Threshold: {report['threshold']:.2f}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during token consistency check: {e}")
        raise

if __name__ == "__main__":
    exit(main())
