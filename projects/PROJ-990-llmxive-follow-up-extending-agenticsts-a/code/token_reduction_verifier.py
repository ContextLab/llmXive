"""
T022a: Token Reduction Verification Logic

Calculates the percentage reduction in token usage between the 'Static All-Layers'
baseline and the 'Dynamic' policy using data from baseline_comparison.csv.
Generates a verification report indicating if the reduction meets the >= 30% threshold.
"""
import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
THRESHOLD_PERCENT = 30.0
INPUT_FILE = "data/processed/baseline_comparison.csv"
OUTPUT_FILE = "data/processed/token_reduction_verification.json"

def load_baseline_comparison(file_path: str) -> pd.DataFrame:
    """
    Loads the baseline comparison CSV and validates required columns.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path.absolute()}")
    
    df = pd.read_csv(path)
    
    required_cols = {'condition', 'avg_tokens'}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Input CSV missing required columns: {missing}")
    
    return df

def calculate_reduction(df: pd.DataFrame) -> Optional[float]:
    """
    Calculates the percentage reduction in tokens:
    (Static_Tokens - Dynamic_Tokens) / Static_Tokens * 100
    
    Returns None if data is missing or invalid.
    """
    static_row = df[df['condition'] == 'Static All-Layers']
    dynamic_row = df[df['condition'] == 'Dynamic']
    
    if static_row.empty or dynamic_row.empty:
        logger.warning("Missing required baseline conditions in data.")
        return None
    
    static_tokens = static_row['avg_tokens'].iloc[0]
    dynamic_tokens = dynamic_row['avg_tokens'].iloc[0]
    
    if pd.isna(static_tokens) or pd.isna(dynamic_tokens):
        logger.warning("NaN values found in token counts.")
        return None
    
    if static_tokens == 0:
        logger.warning("Static token count is zero; cannot calculate percentage reduction.")
        return None
    
    reduction = ((static_tokens - dynamic_tokens) / static_tokens) * 100
    return reduction

def generate_verification_report(reduction: float) -> Dict[str, Any]:
    """
    Generates the verification report dictionary.
    """
    passed = reduction >= THRESHOLD_PERCENT
    return {
        "percentage_reduction": round(reduction, 4),
        "threshold_percent": THRESHOLD_PERCENT,
        "passed": passed,
        "message": f"Token reduction is {reduction:.2f}%. Threshold is {THRESHOLD_PERCENT}%. Verification {'PASSED' if passed else 'FAILED'}."
    }

def save_report(report: Dict[str, Any], output_path: str) -> None:
    """
    Saves the report to a JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Verification report saved to: {path.absolute()}")

def main() -> int:
    """
    Main entry point for the verification script.
    Returns 0 if passed, 1 if failed (to trigger build failure).
    """
    try:
        logger.info(f"Loading baseline comparison from: {INPUT_FILE}")
        df = load_baseline_comparison(INPUT_FILE)
        
        logger.info("Calculating token reduction...")
        reduction = calculate_reduction(df)
        
        if reduction is None:
            logger.error("Could not calculate reduction due to missing or invalid data.")
            return 1
        
        logger.info(f"Calculated reduction: {reduction:.2f}%")
        
        report = generate_verification_report(reduction)
        save_report(report, OUTPUT_FILE)
        
        if not report["passed"]:
            logger.error("Build failure: Token reduction threshold not met.")
            return 1
        
        logger.info("Verification successful.")
        return 0
        
    except Exception as e:
        logger.exception(f"Error during verification: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
