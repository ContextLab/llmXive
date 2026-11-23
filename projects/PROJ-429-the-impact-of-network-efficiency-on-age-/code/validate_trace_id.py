"""
T019: Validate trace_id column in network_metrics.csv.

Validates that the 'trace_id' column exists in data/results/network_metrics.csv
and contains valid SHA-256 hex strings (64 characters, hex digits).

If the file is missing or empty, logs a warning and exits 0 (do not block).
"""
import os
import sys
import logging
import json
import re
from pathlib import Path

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ensure_dirs, get_config_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SHA256_PATTERN = re.compile(r'^[a-f0-9]{64}$')

def validate_trace_id_format(trace_id: str) -> bool:
    """Check if a string is a valid SHA-256 hex string."""
    if not isinstance(trace_id, str):
        return False
    return bool(SHA256_PATTERN.match(trace_id.strip()))

def main():
    """Main entry point for T019 validation."""
    logger.info("Starting T019: Validate trace_id column in network_metrics.csv")
    
    # Ensure output directory exists
    ensure_dirs()
    
    metrics_path = Path("data/results/network_metrics.csv")
    
    # Check if file exists
    if not metrics_path.exists():
        logger.warning(f"File not found: {metrics_path}. T008_run may not have executed. Exiting 0.")
        return 0
    
    # Check if file is empty
    if metrics_path.stat().st_size == 0:
        logger.warning(f"File is empty: {metrics_path}. T008_run may not have produced output. Exiting 0.")
        return 0
    
    try:
        import pandas as pd
        df = pd.read_csv(metrics_path)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        return 1
    
    logger.info(f"Loaded {len(df)} rows from {metrics_path}")
    
    # Check if 'trace_id' column exists
    if 'trace_id' not in df.columns:
        logger.error("Column 'trace_id' is missing from network_metrics.csv")
        return 1
    
    # Validate format of all trace_id values
    valid_count = 0
    invalid_count = 0
    invalid_examples = []
    
    for idx, row in df.iterrows():
        tid = row['trace_id']
        if validate_trace_id_format(tid):
            valid_count += 1
        else:
            invalid_count += 1
            if len(invalid_examples) < 5:
                invalid_examples.append({
                    "row_index": idx,
                    "value": str(tid)[:20] + "..." if len(str(tid)) > 20 else str(tid)
                })
    
    logger.info(f"Validation results: {valid_count} valid, {invalid_count} invalid")
    
    if invalid_count > 0:
        logger.error(f"Found {invalid_count} invalid trace_id values.")
        logger.error("Invalid examples:")
        for ex in invalid_examples:
            logger.error(f"  Row {ex['row_index']}: {ex['value']}")
        return 1
    
    logger.info("SUCCESS: All trace_id values are valid SHA-256 hex strings.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
