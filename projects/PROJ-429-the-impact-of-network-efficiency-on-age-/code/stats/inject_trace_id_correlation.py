"""
Task T028: Inject trace_id into correlation results.

This script reads the output of the correlation analysis (T023_run),
computes a SHA-256 trace_id based on the source code hashes and data
artifact hashes (via version_map), and injects it as a new column
'trace_id' into the CSV file.

Output: Updates data/results/correlation_results.csv in-place.
"""
import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import ensure_dirs, get_config_summary
from state.version_map import (
    load_version_map,
    generate_trace_id,
    update_version_map,
    register_artifact
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths relative to project root
CORRELATION_RESULTS_PATH = PROJECT_ROOT / "data" / "results" / "correlation_results.csv"
VERSION_MAP_PATH = PROJECT_ROOT / "state" / "version_map.json"

def load_correlation_results() -> Optional[pd.DataFrame]:
    """Load the correlation results CSV if it exists."""
    if not CORRELATION_RESULTS_PATH.exists():
        logger.error(f"Correlation results file not found: {CORRELATION_RESULTS_PATH}")
        return None
    
    try:
        df = pd.read_csv(CORRELATION_RESULTS_PATH)
        logger.info(f"Loaded {len(df)} rows from {CORRELATION_RESULTS_PATH}")
        return df
    except Exception as e:
        logger.error(f"Failed to load correlation results: {e}")
        return None

def get_trace_id() -> str:
    """
    Generate a trace_id based on the current state of the version map.
    This ensures reproducibility by linking the output to the exact
    code and data versions used to generate it.
    """
    # Ensure version map exists and is up to date
    if not VERSION_MAP_PATH.exists():
        logger.warning("Version map not found. Initializing empty map.")
        version_map = {"sources": {}, "artifacts": {}, "updated_at": None}
    else:
        version_map = load_version_map(VERSION_MAP_PATH)
    
    # Generate trace_id from the current version map state
    # This effectively hashes the hashes of all tracked files
    trace_id = generate_trace_id(version_map)
    logger.info(f"Generated trace_id: {trace_id[:16]}...")
    return trace_id

def inject_trace_id(df: pd.DataFrame, trace_id: str) -> pd.DataFrame:
    """
    Inject the trace_id into the dataframe as a new column.
    If the column already exists, it will be overwritten.
    """
    df['trace_id'] = trace_id
    logger.info(f"Injected trace_id into column 'trace_id'")
    return df

def save_correlation_results(df: pd.DataFrame) -> bool:
    """Save the updated dataframe back to the CSV file."""
    try:
        ensure_dirs(CORRELATION_RESULTS_PATH)
        df.to_csv(CORRELATION_RESULTS_PATH, index=False)
        logger.info(f"Saved updated results to {CORRELATION_RESULTS_PATH}")
        
        # Register the updated artifact in the version map
        version_map = load_version_map(VERSION_MAP_PATH)
        register_artifact(
            version_map,
            "correlation_results",
            CORRELATION_RESULTS_PATH,
            "CSV"
        )
        update_version_map(version_map, VERSION_MAP_PATH)
        
        return True
    except Exception as e:
        logger.error(f"Failed to save correlation results: {e}")
        return False

def main():
    """Main entry point for T028."""
    logger.info("Starting T028: Inject trace_id into correlation results")
    
    # Load data
    df = load_correlation_results()
    if df is None:
        logger.error("Cannot proceed without correlation results data.")
        sys.exit(1)
    
    # Check if trace_id already exists to avoid redundant work
    if 'trace_id' in df.columns:
        logger.info("Column 'trace_id' already exists. Overwriting with fresh trace.")
    
    # Generate trace_id
    trace_id = get_trace_id()
    
    # Inject trace_id
    df = inject_trace_id(df, trace_id)
    
    # Save results
    if not save_correlation_results(df):
        logger.error("Failed to save updated correlation results.")
        sys.exit(1)
    
    logger.info("T028 completed successfully.")

if __name__ == "__main__":
    main()
