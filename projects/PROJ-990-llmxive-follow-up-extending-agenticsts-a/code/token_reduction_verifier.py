import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
THRESHOLD_PERCENT = 30.0
INPUT_FILE = "data/processed/baseline_comparison.csv"
OUTPUT_FILE = "data/processed/token_reduction_verification.json"
FAILURE_FILE = "data/processed/verification_failed.json"

def load_baseline_comparison(filepath: str) -> pd.DataFrame:
    """
    Load the baseline comparison CSV.
    Expects columns: condition, win_rate, avg_tokens, std_dev_tokens
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {filepath}")
    
    df = pd.read_csv(path)
    
    required_cols = ['condition', 'win_rate', 'avg_tokens', 'std_dev_tokens']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {filepath}: {missing}")
    
    return df

def calculate_reduction(df: pd.DataFrame) -> float:
    """
    Calculate the percentage reduction in token usage for the Dynamic policy
    compared to the Static All-Layers baseline.
    
    Formula: ((Static_Avg_Tokens - Dynamic_Avg_Tokens) / Static_Avg_Tokens) * 100
    """
    # Identify rows
    static_row = df[df['condition'] == 'Static']
    dynamic_row = df[df['condition'] == 'Dynamic']
    
    if static_row.empty:
        raise ValueError("No 'Static' condition found in baseline comparison.")
    if dynamic_row.empty:
        raise ValueError("No 'Dynamic' condition found in baseline comparison.")
    
    static_tokens = static_row['avg_tokens'].iloc[0]
    dynamic_tokens = dynamic_row['avg_tokens'].iloc[0]
    
    if static_tokens <= 0:
        raise ValueError(f"Static avg_tokens must be > 0, got {static_tokens}")
    
    reduction = ((static_tokens - dynamic_tokens) / static_tokens) * 100.0
    return float(reduction)

def generate_verification_report(actual_reduction: float, passed: bool) -> Dict[str, Any]:
    """
    Generate the verification report dictionary.
    """
    return {
        "passed": passed,
        "actual_reduction_percent": actual_reduction,
        "threshold_percent": THRESHOLD_PERCENT
    }

def save_report(report: Dict[str, Any], filepath: str) -> None:
    """
    Save the verification report to a JSON file.
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Verification report saved to {filepath}")

def generate_failure_artifact(actual_reduction: float) -> None:
    """
    Generate a failure artifact if the reduction threshold is not met.
    """
    failure_data = {
        "status": "FAILED",
        "reason": "Token reduction threshold not met",
        "actual_reduction_percent": actual_reduction,
        "required_threshold_percent": THRESHOLD_PERCENT,
        "message": f"Actual reduction ({actual_reduction:.2f}%) is less than required ({THRESHOLD_PERCENT}%)."
    }
    save_report(failure_data, FAILURE_FILE)
    logger.error(f"Failure artifact generated: {FAILURE_FILE}")

def main() -> int:
    """
    Main entry point for the token reduction verification task.
    
    Returns:
        int: 0 if passed, 1 if failed (enforcing SC-002 hard gate).
    """
    logger.info(f"Starting token reduction verification. Input: {INPUT_FILE}")
    
    try:
        # Load data
        df = load_baseline_comparison(INPUT_FILE)
        
        # Calculate reduction
        reduction = calculate_reduction(df)
        logger.info(f"Calculated token reduction: {reduction:.2f}%")
        
        # Check threshold
        passed = reduction >= THRESHOLD_PERCENT
        
        # Generate report
        report = generate_verification_report(reduction, passed)
        save_report(report, OUTPUT_FILE)
        
        if passed:
            logger.info(f"SUCCESS: Token reduction ({reduction:.2f}%) meets threshold ({THRESHOLD_PERCENT}%).")
            return 0
        else:
            logger.error(f"FAILURE: Token reduction ({reduction:.2f}%) does not meet threshold ({THRESHOLD_PERCENT}%).")
            generate_failure_artifact(reduction)
            return 1
            
    except Exception as e:
        logger.error(f"Error during verification: {e}")
        # If we can't even calculate, we fail the gate
        return 1

if __name__ == "__main__":
    sys.exit(main())
