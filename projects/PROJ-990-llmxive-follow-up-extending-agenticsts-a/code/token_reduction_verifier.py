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

BASELINE_COMPARISON_PATH = Path("data/processed/baseline_comparison.csv")
OUTPUT_PATH = Path("data/processed/token_reduction_verification.json")
THRESHOLD = 0.30  # 30% reduction required

def load_baseline_comparison() -> pd.DataFrame:
    """
    Load the baseline comparison CSV.
    Expected columns: condition, win_rate, avg_tokens, std_dev_tokens
    """
    if not BASELINE_COMPARISON_PATH.exists():
        raise FileNotFoundError(
            f"Required input file not found: {BASELINE_COMPARISON_PATH}. "
            "Ensure T022 has been executed successfully."
        )
    
    df = pd.read_csv(BASELINE_COMPARISON_PATH)
    required_cols = {'condition', 'win_rate', 'avg_tokens', 'std_dev_tokens'}
    if not required_cols.issubset(df.columns):
        raise ValueError(
            f"Input CSV missing required columns. Expected: {required_cols}, "
            f"Found: {set(df.columns)}"
        )
    return df

def calculate_reduction(df: pd.DataFrame) -> float:
    """
    Calculate the percentage reduction in token usage between Dynamic and Static policies.
    Formula: ((Static_Avg_Tokens - Dynamic_Avg_Tokens) / Static_Avg_Tokens) * 100
    
    Raises:
        ValueError: If 'Static' or 'Dynamic' conditions are missing.
    """
    # Filter for relevant conditions
    static_row = df[df['condition'] == 'Static']
    dynamic_row = df[df['condition'] == 'Dynamic']

    if static_row.empty:
        raise ValueError("Input data missing 'Static' baseline condition.")
    if dynamic_row.empty:
        raise ValueError("Input data missing 'Dynamic' policy condition.")
    
    static_tokens = static_row['avg_tokens'].iloc[0]
    dynamic_tokens = dynamic_row['avg_tokens'].iloc[0]
    
    if static_tokens <= 0:
        raise ValueError(f"Static avg_tokens must be > 0, got {static_tokens}")
    
    reduction = ((static_tokens - dynamic_tokens) / static_tokens) * 100.0
    return float(reduction)

    if static_tokens <= 0:
        raise ValueError(f"Static avg_tokens must be positive, got {static_tokens}")

    reduction = ((static_tokens - dynamic_tokens) / static_tokens) * 100.0
    return reduction

def generate_verification_report(reduction_percent: float) -> Dict[str, Any]:
    """
    Generate the verification report dictionary.
    """
    passed = reduction_percent >= (THRESHOLD * 100)
    
    report = {
        "passed": passed,
        "actual_reduction_percent": round(reduction_percent, 4),
        "threshold_percent": THRESHOLD * 100,
        "message": "Success" if passed else "Failed: Token reduction below 30% threshold"
    }

def save_report(report: Dict[str, Any]) -> None:
    """
    Save the report to the output JSON file.
    """
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Verification report saved to {OUTPUT_PATH}")

def main():
    """
    Main entry point for T022a.
    Loads baseline comparison, calculates reduction, and enforces the hard gate.
    """
    logger.info("Starting Token Reduction Verification (T022a)")
    
    try:
        # 1. Load Data
        df = load_baseline_comparison()
        logger.info(f"Loaded baseline comparison with {len(df)} rows.")
        
        # 2. Calculate Reduction
        reduction = calculate_reduction(df)
        logger.info(f"Calculated token reduction: {reduction:.2f}%")
        
        # 3. Generate Report
        report = generate_verification_report(reduction)
        
        # 4. Save Report
        save_report(report)
        
        # 5. Enforce Hard Gate (SC-002)
        if not report['passed']:
            logger.error(f"CRITICAL: Token reduction ({reduction:.2f}%) is below threshold ({THRESHOLD*100}%).")
            logger.error("Pipeline halted due to failure of Success Criterion SC-002.")
            sys.exit(1)
        
        logger.info("Token reduction verification PASSED. Pipeline continues.")
        
    except FileNotFoundError as e:
        logger.error(f"Data source missing: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
