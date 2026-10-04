"""
Task T014b: VALIDITY METRICS

Calculates the percentage of valid records (age >= 65, non-null metrics, MMSE >= 24 if available)
vs total raw input records from data/raw/raw_dataset.csv.
Writes the calculated percentage to data/processed/validity_metrics.json.

Depends on: T012c (exclusion_log.json)
"""
import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any

from config import get_config, ensure_dirs
from utils import setup_logging, log_info, log_warning, log_error, get_timestamp

def get_config_paths() -> Dict[str, Path]:
    """Get standard paths from config."""
    cfg = get_config()
    return {
        "raw_dataset": cfg["paths"]["raw_dataset"],
        "exclusion_log": cfg["paths"]["processed_dir"] / "exclusion_log.json",
        "validity_metrics": cfg["paths"]["processed_dir"] / "validity_metrics.json",
    }

def load_raw_count(raw_path: Path) -> int:
    """Load raw dataset and return total row count."""
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw dataset not found at {raw_path}")
    df = pd.read_csv(raw_path)
    return len(df)

def load_exclusion_log(log_path: Path) -> Dict[str, Any]:
    """Load exclusion log to get exclusion counts."""
    if not log_path.exists():
        raise FileNotFoundError(f"Exclusion log not found at {log_path}")
    with open(log_path, "r") as f:
        return json.load(f)

def calculate_validity_metrics(
    total_raw: int, exclusion_log: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate validity metrics based on total raw records and exclusion log.
    
    Valid records = Total Raw - Excluded Records
    Excluded records are summed from the exclusion log keys:
    ERR_MISSING_AGE_FIELD, ERR_MISSING_SCORE, ERR_MMSE_IMPAIRED
    """
    excluded_count = 0
    exclusion_keys = [
        "ERR_MISSING_AGE_FIELD",
        "ERR_MISSING_SCORE",
        "ERR_MMSE_IMPAIRED",
    ]
    
    for key in exclusion_keys:
        count = exclusion_log.get(key, 0)
        if isinstance(count, int):
            excluded_count += count
        elif isinstance(count, dict):
            # Handle nested structures if any, though log is usually flat counts
            excluded_count += count.get("count", 0)

    valid_count = total_raw - excluded_count
    
    # Ensure non-negative
    if valid_count < 0:
        valid_count = 0
        log_warning("Calculated valid count is negative; setting to 0.")

    validity_percentage = (valid_count / total_raw * 100) if total_raw > 0 else 0.0

    return {
        "total_raw_records": total_raw,
        "total_excluded_records": excluded_count,
        "valid_records": valid_count,
        "validity_percentage": round(validity_percentage, 2),
        "timestamp": get_timestamp(),
        "simulation_mode": exclusion_log.get("SIMULATION_FALLBACK", False),
    }

def save_validity_metrics(metrics: Dict[str, Any], output_path: Path) -> None:
    """Save validity metrics to JSON file."""
    ensure_dirs(output_path)
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)
    log_info(f"Validity metrics saved to {output_path}")

def main() -> None:
    """Main entry point for T014b."""
    setup_logging()
    log_info("Starting T014b: Validity Metrics Calculation")
    
    try:
        paths = get_config_paths()
        
        # Load total raw count
        log_info(f"Loading raw dataset from {paths['raw_dataset']}")
        total_raw = load_raw_count(paths["raw_dataset"])
        log_info(f"Total raw records: {total_raw}")
        
        # Load exclusion log
        log_info(f"Loading exclusion log from {paths['exclusion_log']}")
        exclusion_log = load_exclusion_log(paths["exclusion_log"])
        
        # Calculate metrics
        log_info("Calculating validity metrics...")
        metrics = calculate_validity_metrics(total_raw, exclusion_log)
        
        # Save results
        save_validity_metrics(metrics, paths["validity_metrics"])
        
        log_info("T014b completed successfully.")
        
    except FileNotFoundError as e:
        log_error(f"File not found: {e}")
        raise
    except Exception as e:
        log_error(f"Error during validity metrics calculation: {e}")
        raise

if __name__ == "__main__":
    main()
