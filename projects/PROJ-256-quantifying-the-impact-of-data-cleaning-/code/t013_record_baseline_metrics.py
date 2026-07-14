import os
import sys
import json
import logging
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime

from utils import setup_logging, compute_file_checksum
from analysis import run_baseline_analysis

logger = logging.getLogger(__name__)

def format_metric_value(value: Any, precision: int = 3) -> Any:
    """Format numeric values to specified precision."""
    if value is None:
        return None
    if isinstance(value, float):
        return round(value, precision)
    if isinstance(value, list):
        return [format_metric_value(v, precision) for v in value]
    return value

def isfinite(value: Any) -> bool:
    """Check if value is finite."""
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return float(value) != float('inf') and float(value) != float('-inf') and not (isinstance(value, float) and value != value) # nan check
    if isinstance(value, list):
        return all(isfinite(v) for v in value)
    return True

def log_metrics_summary(metrics: Dict[str, Any]):
    """Log summary of metrics."""
    datasets = metrics.get("datasets", [])
    logger.info(f"Processed {len(datasets)} datasets.")
    for ds in datasets:
        name = ds.get("dataset_name", "unknown")
        logger.info(f"  - {name}: {ds.get('n_rows', 0)} rows")
        if "t_test" in ds and "p_value" in ds["t_test"]:
            p = ds["t_test"]["p_value"]
            if p is not None and isfinite(p):
                logger.info(f"    T-test p-value: {p:.4f}")
        if "regression" in ds and "r_squared" in ds["regression"]:
            r2 = ds["regression"]["r_squared"]
            if r2 is not None and isfinite(r2):
                logger.info(f"    R-squared: {r2:.4f}")

def process_dataset_for_baseline(raw_dir: str, output_file: str, config: Dict[str, Any]) -> bool:
    """
    Process datasets from raw_dir and record metrics to output_file.
    Ensures precision >= 3 decimal places.
    """
    # Run analysis
    result = run_baseline_analysis(raw_dir, output_file, config)
    
    if not isinstance(result, bool) or not result:
        logger.error("Analysis failed or returned invalid result.")
        return False

    # Load and re-save with explicit precision formatting to ensure requirement
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        # Format all floats
        def format_recursive(obj):
            if isinstance(obj, dict):
                return {k: format_recursive(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [format_recursive(v) for v in obj]
            elif isinstance(obj, float):
                if not (obj != obj): # not nan
                    return round(obj, 3)
            return obj

        formatted_data = format_recursive(data)
        
        # Write back
        with open(output_file, 'w') as f:
            json.dump(formatted_data, f, indent=2)
        
        logger.info(f"Metrics formatted and saved to {output_file}")
        return True
    
    return False

def main():
    """Main entry point for T013."""
    setup_logging("INFO")
    
    raw_dir = os.environ.get("RAW_DATA_PATH", "data/raw")
    output_file = os.environ.get("OUTPUT_PATH", "data/processed/baseline_metrics.json")
    
    if not os.path.isdir(raw_dir):
        logger.error(f"Raw data directory not found: {raw_dir}")
        sys.exit(1)

    config = {
        "outcome_col": os.environ.get("OUTCOME_COL", "target"),
        "group_col": os.environ.get("GROUP_COL", "group")
    }

    success = process_dataset_for_baseline(raw_dir, output_file, config)
    if success:
        logger.info("T013 completed successfully.")
    else:
        logger.error("T013 failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
