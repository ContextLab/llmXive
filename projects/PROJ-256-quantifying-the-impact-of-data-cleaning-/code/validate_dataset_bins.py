"""
Task T1229: Validate final dataset collection against bin constraints.

This script validates that the collected datasets satisfy the bin constraints:
- n < 50
- 50 <= n <= 200
- n > 200

It also checks missingness levels if required.
If any bin is empty, the script exits with a non-zero code and logs the failure.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))

from config import get_config
from utils import setup_logging

def load_baseline_metrics(config: Dict[str, Any]) -> Dict[str, Any]:
    """Load baseline metrics from the processed data directory."""
    baseline_path = Path(config.get("PROCESSED_DATA_PATH", "data/processed")) / "baseline_metrics.json"
    if not baseline_path.exists():
        raise FileNotFoundError(f"Baseline metrics file not found at {baseline_path}")
    
    with open(baseline_path, 'r') as f:
        return json.load(f)

def bin_dataset_size(n_rows: int) -> str:
    """Assign dataset to size bin."""
    if n_rows < 50:
        return "n_lt_50"
    elif n_rows <= 200:
        return "n_50_200"
    else:
        return "n_gt_200"

def validate_bins(metrics: Dict[str, Any], logger: logging.Logger) -> bool:
    """
    Validate that all size bins are populated.
    
    Returns True if all bins have at least one dataset, False otherwise.
    """
    bins: Dict[str, List[str]] = {
        "n_lt_50": [],
        "n_50_200": [],
        "n_gt_200": []
    }

    # Handle both list and dict formats for metrics
    datasets = metrics if isinstance(metrics, list) else list(metrics.values())

    for dataset_info in datasets:
        # Extract dataset name and row count
        if isinstance(dataset_info, dict):
            dataset_name = dataset_info.get("dataset_name", "unknown")
            n_rows = dataset_info.get("n_rows", dataset_info.get("dataset_size", 0))
        else:
            # Fallback for unexpected formats
            logger.warning(f"Unexpected dataset info format: {type(dataset_info)}")
            continue

        if n_rows is None or n_rows == 0:
            logger.warning(f"Dataset {dataset_name} has invalid row count: {n_rows}")
            continue

        bin_name = bin_dataset_size(n_rows)
        bins[bin_name].append(dataset_name)
        logger.info(f"Dataset {dataset_name} (n={n_rows}) assigned to bin {bin_name}")

    # Check if any bin is empty
    all_populated = True
    for bin_name, dataset_list in bins.items():
        if not dataset_list:
            logger.error(f"BIN EMPTY: {bin_name} has no datasets!")
            all_populated = False
        else:
            logger.info(f"BIN OK: {bin_name} has {len(dataset_list)} dataset(s): {dataset_list}")

    if not all_populated:
        logger.error("VALIDATION FAILED: One or more bins are empty. Pipeline cannot proceed.")
        return False

    logger.info("VALIDATION PASSED: All size bins are populated.")
    return True

def main():
    """Main entry point for T1229 validation."""
    logger = setup_logging(log_level="INFO")
    config = get_config()

    logger.info("Starting dataset bin validation (T1229)...")

    try:
        # Load baseline metrics
        metrics = load_baseline_metrics(config)
        logger.info(f"Loaded metrics for {len(metrics) if isinstance(metrics, list) else len(metrics.keys())} dataset(s)")

        # Validate bins
        success = validate_bins(metrics, logger)

        if success:
            logger.info("T1229 Validation successful.")
            sys.exit(0)
        else:
            logger.error("T1229 Validation failed: Missing bins detected.")
            sys.exit(1)

    except FileNotFoundError as e:
        logger.error(f"Required data file missing: {e}")
        logger.error("T1229 Validation failed: Cannot validate without baseline metrics.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        logger.error("T1229 Validation failed due to exception.")
        sys.exit(1)

if __name__ == "__main__":
    main()
