"""
Validator module for T008c.
Checks sample count from utility labels and triggers fallback logic if n < 300.
"""
import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

from config import load_config_from_file, ensure_directories
from extractor import load_ablation_results, convert_to_dataframe

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MIN_SAMPLE_THRESHOLD = 300
FALLBACK_K = 2
OUTPUT_FILE = "data/processed/validation_status.json"

def check_sample_count(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check the sample count of the utility labels dataframe.
    
    Args:
        df: DataFrame containing utility labels (output of T008b).
        
    Returns:
        Dictionary containing validation status, sample count, and fallback flags.
    """
    if df is None or df.empty:
        logger.error("Input dataframe is empty or None.")
        return {
            "valid": False,
            "sample_count": 0,
            "fallback_triggered": True,
            "fallback_reason": "Empty dataset",
            "k_value": FALLBACK_K
        }

    n = len(df)
    logger.info(f"Validating sample count: n = {n}")

    result = {
        "valid": True,
        "sample_count": n,
        "fallback_triggered": False,
        "fallback_reason": None,
        "k_value": None
    }

    if n < MIN_SAMPLE_THRESHOLD:
        result["valid"] = False
        result["fallback_triggered"] = True
        result["fallback_reason"] = f"Sample count ({n}) is below threshold ({MIN_SAMPLE_THRESHOLD})"
        result["k_value"] = FALLBACK_K
        logger.warning(
            f"⚠️ Sample count ({n}) is below threshold ({MIN_SAMPLE_THRESHOLD}). "
            f"Triggering fallback to heuristic (fixed k={FALLBACK_K})."
        )
    else:
        logger.info(f"Sample count ({n}) meets threshold ({MIN_SAMPLE_THRESHOLD}). No fallback needed.")

    return result

def run_validation(
    input_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main entry point to run validation on utility labels.
    
    Args:
        input_path: Path to the utility_labels.csv (output of T008b).
                    Defaults to data/processed/utility_labels.csv.
        output_path: Path to write the validation status JSON.
                     Defaults to data/processed/validation_status.json.
                     
    Returns:
        The validation result dictionary.
    """
    config = load_config_from_file()
    ensure_directories()

    if input_path is None:
        input_path = str(Path(config.get("paths", {}).get("processed_data_dir", "data/processed")) / "utility_labels.csv")
    
    if output_path is None:
        output_path = str(Path(config.get("paths", {}).get("processed_data_dir", "data/processed")) / "validation_status.json")

    logger.info(f"Loading utility labels from: {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}. "
                                "Ensure T008b (extractor) has completed successfully.")

    df = convert_to_dataframe(input_path)
    
    validation_result = check_sample_count(df)
    
    # Write result to output file
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    with open(output_path, 'w') as f:
        json.dump(validation_result, f, indent=2)
        
    logger.info(f"Validation status written to: {output_path}")
    
    return validation_result

def main():
    """CLI entry point."""
    try:
        result = run_validation()
        print(json.dumps(result, indent=2))
        
        # Exit with non-zero code if fallback was triggered to signal downstream dependencies
        if result.get("fallback_triggered"):
            logger.warning("Fallback triggered. Downstream tasks should handle k=FALLBACK_K.")
            # Note: We do not exit with error code here as the task is to *trigger* the fallback,
            # not to fail the pipeline. The pipeline logic in T015/T016 will consume this status.
            
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise

if __name__ == "__main__":
    main()
