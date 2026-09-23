import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

# Import logging configuration
from logging_config import setup_logging, get_logger

# Initialize logger
logger = get_logger(__name__)

# Constants for thresholds
MINIMUM_THRESHOLD = 100
FULL_STUDY_THRESHOLD = 300

def load_aggregated_data(file_path: str) -> Optional[Dict[str, Any]]:
    """Load the aggregated clean CSV data (simulated as dict for record counting)."""
    # In a real implementation, this would read the CSV.
    # Since T016a is marked done, we assume record_counts.json exists or we read the CSV.
    # We will read the CSV to get the count dynamically if the JSON is missing,
    # but primarily rely on the output of T016a if available.
    try:
        import pandas as pd
        df = pd.read_csv(file_path)
        return {"total_records": len(df), "data": df}
    except Exception as e:
        logger.error(f"Failed to load aggregated data: {e}")
        return None

def extract_source_metadata(data: Dict[str, Any]) -> List[str]:
    """Extract source metadata from the loaded data."""
    # Placeholder for metadata extraction logic
    return []

def count_records(data: Dict[str, Any]) -> Dict[str, int]:
    """Count total, normalized, and raw records."""
    total = data.get("total_records", 0)
    # In a real scenario, we would filter by 'normalization_method' column
    # For now, assuming the data dict has pre-calculated counts or we parse the dataframe
    df = data.get("data")
    if df is not None and 'normalization_method' in df.columns:
        normalized_count = len(df[df['normalization_method'] == 'archard'])
        raw_count = len(df[df['normalization_method'] == 'raw'])
    else:
        # Fallback if column missing or data not loaded as DF
        normalized_count = 0
        raw_count = 0
    return {
        "total_count": total,
        "normalized_count": normalized_count,
        "raw_count": raw_count
    }

def log_source_warning(data: Dict[str, Any]) -> None:
    """Log warning if data sources are insufficient."""
    # Placeholder logic
    pass

def compare_thresholds(normalized_count: int) -> Dict[str, Any]:
    """
    Compare normalized_count against defined thresholds.
    
    Logic:
    - If normalized_count < 100 (SC-006): HALT (exit code 1).
    - If 100 <= normalized_count < 300 (SC-004): Scope degradation warning (exit code 2).
    - Else: Full study scope.
    
    Returns a dictionary with the study scope and flags.
    """
    result = {
        "normalized_count": normalized_count,
        "study_scope": "unknown",
        "halt_requested": False,
        "scope_degradation": False,
        "warning_message": None,
        "exit_code": 0
    }

    if normalized_count < MINIMUM_THRESHOLD:
        result["study_scope"] = "insufficient_data"
        result["halt_requested"] = True
        result["exit_code"] = 1
        result["warning_message"] = f"CRITICAL: Normalized record count ({normalized_count}) is below minimum threshold ({MINIMUM_THRESHOLD}) per SC-006. Halting execution."
        logger.critical(result["warning_message"])
    elif normalized_count < FULL_STUDY_THRESHOLD:
        result["study_scope"] = "pilot_study"
        result["scope_degradation"] = True
        result["exit_code"] = 2
        result["warning_message"] = f"WARNING: Normalized record count ({normalized_count}) is below full study threshold ({FULL_STUDY_THRESHOLD}). Scope degraded to 'pilot_study' per SC-004."
        logger.warning(result["warning_message"])
    else:
        result["study_scope"] = "full_study"
        logger.info(f"Normalized record count ({normalized_count}) meets full study threshold. Scope: 'full_study'.")

    return result

def main():
    """
    Main entry point for T016b: compare_thresholds.
    Reads record counts, compares against thresholds, and exits with appropriate code.
    """
    setup_logging()
    
    # Paths
    processed_dir = Path("data/processed")
    input_file = processed_dir / "aggregated_clean.csv"
    output_file = processed_dir / "threshold_check.json"
    
    # Ensure output directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load Data
    logger.info(f"Loading aggregated data from {input_file}...")
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)

    data = load_aggregated_data(str(input_file))
    if data is None:
        logger.error("Failed to load data.")
        sys.exit(1)

    # 2. Count Records
    # Note: T016a should have produced record_counts.json, but we calculate here to be robust
    # or we could load T016a's output. The task asks to compare the count.
    counts = count_records(data)
    normalized_count = counts.get("normalized_count", 0)
    
    logger.info(f"Normalized record count: {normalized_count}")

    # 3. Compare Thresholds
    threshold_result = compare_thresholds(normalized_count)

    # 4. Write Output
    try:
        with open(output_file, 'w') as f:
            json.dump(threshold_result, f, indent=2)
        logger.info(f"Threshold check results written to {output_file}")
    except Exception as e:
        logger.error(f"Failed to write output file: {e}")
        sys.exit(1)

    # 5. Exit with appropriate code
    exit_code = threshold_result.get("exit_code", 0)
    if exit_code != 0:
        sys.exit(exit_code)
    
    return threshold_result

if __name__ == "__main__":
    main()