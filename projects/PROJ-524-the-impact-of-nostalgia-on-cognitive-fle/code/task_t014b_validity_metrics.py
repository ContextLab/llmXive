"""
Task T014b: Calculate validity metrics.

Calculates the percentage of valid records (age >= 65, non-null metrics,
MMSE >= 24 if available) vs total raw input records.
Writes results to data/processed/validity_metrics.json.
"""
import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any

# Import from local utils for logging setup
from utils import setup_logging, log_info, log_warning, log_error, get_timestamp

# Import config for paths
from config import get_config

def load_exclusion_log() -> Dict[str, Any]:
    """Load the exclusion log generated in T012c."""
    config = get_config()
    log_path = config["paths"]["processed_dir"] / "exclusion_log.json"
    
    if not log_path.exists():
        raise FileNotFoundError(f"Exclusion log not found at {log_path}. Run T012c first.")
    
    with open(log_path, 'r') as f:
        return json.load(f)

def load_raw_count() -> int:
    """Load the total count of raw records from data/raw/raw_dataset.csv."""
    config = get_config()
    raw_path = config["paths"]["raw_dir"] / "raw_dataset.csv"
    
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw dataset not found at {raw_path}. Run T010b first.")
    
    # Count rows efficiently without loading full dataframe if possible, 
    # but pandas read_csv is fine for this size.
    df = pd.read_csv(raw_path)
    return len(df)

def calculate_validity_metrics(exclusion_log: Dict[str, Any], raw_count: int) -> Dict[str, Any]:
    """
    Calculate validity percentage based on exclusion log.
    
    Valid records = Total Raw - (Excluded Age + Excluded Score + Excluded MMSE)
    Note: The exclusion log contains counts of records removed at each step.
    """
    # Extract counts from exclusion log
    excluded_age = exclusion_log.get("ERR_MISSING_AGE_FIELD", 0)
    excluded_score = exclusion_log.get("ERR_MISSING_SCORE", 0)
    excluded_mmse = exclusion_log.get("ERR_MMSE_IMPAIRED", 0)
    
    # Note: If SIMULATION_FALLBACK is present, it's a flag, not a count to subtract 
    # from the valid set in the same way, but we track it.
    
    total_excluded = excluded_age + excluded_score + excluded_mmse
    valid_count = raw_count - total_excluded
    
    if raw_count == 0:
        validity_pct = 0.0
    else:
        validity_pct = (valid_count / raw_count) * 100
    
    target_met = validity_pct >= 90.0
    
    return {
        "raw_record_count": raw_count,
        "valid_record_count": valid_count,
        "validity_percentage": round(validity_pct, 2),
        "target_met": target_met,
        "breakdown": {
            "excluded_age": excluded_age,
            "excluded_score": excluded_score,
            "excluded_mmse": excluded_mmse,
            "total_excluded": total_excluded
        }
    }

def main():
    """Main entry point for T014b."""
    logger = setup_logging("T014b_validity_metrics")
    logger.info(f"Starting validity metrics calculation at {get_timestamp()}")
    
    try:
        # Load dependencies
        exclusion_log = load_exclusion_log()
        logger.info("Loaded exclusion log from T012c")
        
        raw_count = load_raw_count()
        logger.info(f"Loaded raw record count: {raw_count}")
        
        # Calculate metrics
        metrics = calculate_validity_metrics(exclusion_log, raw_count)
        
        # Save results
        config = get_config()
        output_path = config["paths"]["processed_dir"] / "validity_metrics.json"
        
        with open(output_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Valid metrics saved to {output_path}")
        logger.info(f"Validity: {metrics['validity_percentage']}% (Target Met: {metrics['target_met']})")
        
        if not metrics['target_met']:
            log_warning(f"Validity target (>=90%) NOT met. Current: {metrics['validity_percentage']}%")
        
        return 0
        
    except FileNotFoundError as e:
        log_error(f"Missing required input file: {e}")
        return 1
    except Exception as e:
        log_error(f"Unexpected error during validity metrics calculation: {e}")
        raise

if __name__ == "__main__":
    exit(main())
