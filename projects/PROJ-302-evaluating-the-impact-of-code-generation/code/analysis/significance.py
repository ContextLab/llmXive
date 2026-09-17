"""
Significance Flagging Module (T020)

Implements statistical significance checking and writes the result to a JSON artifact.
Depends on: T024 (statistical_test.py) for p-values.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root path (assumes code/analysis/ is 3 levels deep)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def check_significance(p_val: float, alpha: float = 0.05) -> bool:
    """
    Check if a p-value indicates statistical significance.

    Args:
        p_val (float): The p-value obtained from a statistical test.
        alpha (float): The significance threshold (default 0.05).

    Returns:
        bool: True if p_val < alpha, False otherwise.
    """
    if not isinstance(p_val, (int, float)):
        raise TypeError(f"p_val must be a number, got {type(p_val)}")
    if not (0.0 <= p_val <= 1.0):
        logger.warning(f"p_val {p_val} is outside valid range [0, 1].")
    
    return p_val < alpha


def write_significance_flag(p_val: float, alpha: float = 0.05, output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Determine significance and write the result to a JSON file.

    Args:
        p_val (float): The p-value to check.
        alpha (float): The significance threshold.
        output_path (Optional[Path]): Path to the output JSON file. 
                                   Defaults to data/processed/significance_flag.json.

    Returns:
        Dict[str, Any]: The result dictionary containing 'is_significant', 'p_value', 'alpha'.
    """
    if output_path is None:
        output_path = DATA_PROCESSED_DIR / "significance_flag.json"
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    is_sig = check_significance(p_val, alpha)
    
    result = {
        "is_significant": is_sig,
        "p_value": float(p_val),
        "alpha": float(alpha)
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Significance check complete. P-value: {p_val}, Alpha: {alpha}, Significant: {is_sig}")
    logger.info(f"Results written to: {output_path}")

    return result


def main():
    """
    Main entry point for the significance flagging task.
    
    This function loads the p-value from the T024 output 
    (analysis_results.json) and writes the significance flag.
    If the input file is missing, it exits with an error to enforce
    the dependency on T024 (no silent fallback).
    """
    logger.info("Starting Significance Flagging (T020)...")

    # Attempt to load p-value from T024 output
    # T024 (statistical_test.py) typically outputs to data/processed/analysis_results.json
    input_file = DATA_PROCESSED_DIR / "analysis_results.json"
    
    p_val = None

    if input_file.exists():
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Try common keys where p-value might be stored
            p_val = data.get("p_value") or data.get("p_val")
            if p_val is None and "results" in data:
                p_val = data["results"].get("p_value") or data["results"].get("p_val")
            
            if p_val is None:
                logger.error(f"Could not find 'p_value' key in {input_file}.")
                sys.exit(1)
            
            logger.info(f"Loaded p-value {p_val} from {input_file}")
        except Exception as e:
            logger.error(f"Failed to parse {input_file}: {e}")
            sys.exit(1)
    else:
        logger.error(f"Input file {input_file} not found. T024 (statistical_test) must run first.")
        sys.exit(1)

    # Run the check and write output
    try:
        result = write_significance_flag(p_val=p_val, alpha=0.05)
        logger.info("Task T020 completed successfully.")
        return result
    except Exception as e:
        logger.error(f"Task T020 failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()