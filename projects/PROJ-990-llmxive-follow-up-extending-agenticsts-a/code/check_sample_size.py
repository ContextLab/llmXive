"""
Task T008c: Sample Count Check and Fallback Flag.

Logic:
1. Count rows in `data/processed/ablation_labels_train.json` (from T008).
2. If n < 300:
   - Log to `data/processed/edge_case_warnings.log` with exact text:
     "Warning: statistical power is marginal (n={n}); recommend expanding the dataset"
   - Generate `data/processed/fallback_flag.json` with content:
     {"fallback": true, "use_heuristic": true, "reason": "n < 300"}
3. If n >= 300:
   - Generate `data/processed/fallback_flag.json` with content:
     {"fallback": false, "use_heuristic": false}
"""
import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging to append to the specific warning file
WARNING_LOG_PATH = Path("data/processed/edge_case_warnings.log")
FALLBACK_FLAG_PATH = Path("data/processed/fallback_flag.json")
ABLATION_TRAIN_LABELS_PATH = Path("data/processed/ablation_labels_train.json")

# Ensure logging directory exists
WARNING_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

# Setup logger specifically for warnings
logger = logging.getLogger("T008c_SampleCheck")
logger.setLevel(logging.WARNING)

# Remove existing handlers to avoid duplicates
logger.handlers = []

# File handler for the specific warning log
fh = logging.FileHandler(WARNING_LOG_PATH, mode='a', encoding='utf-8')
fh.setLevel(logging.WARNING)
formatter = logging.Formatter('%(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

# Console handler for visibility during execution
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)


def load_ablation_labels(path: Path) -> List[Dict[str, Any]]:
    """
    Load ablation labels from a JSON file.
    Returns a list of records.
    """
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        # If it's a dict with a specific key, try to extract the list
        if isinstance(data, dict) and len(data) == 1:
            first_key = list(data.keys())[0]
            if isinstance(data[first_key], list):
                data = data[first_key]
            else:
                raise ValueError(f"Unexpected structure in {path}: expected a list or a dict containing a single list value.")
        else:
            raise ValueError(f"Unexpected structure in {path}: expected a list of records.")
    
    return data


def log_warning(message: str) -> None:
    """Log a warning message to the file and console."""
    logger.warning(message)


def write_fallback_flag(flag_data: Dict[str, Any], path: Path) -> None:
    """Write the fallback flag JSON to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(flag_data, f, indent=2)
    logger.info(f"Fallback flag written to {path}")


def main() -> int:
    """
    Main entry point for T008c.
    Returns 0 on success, 1 on critical failure (e.g., missing input).
    """
    try:
        # Check if input file exists
        if not ABLATION_TRAIN_LABELS_PATH.exists():
            logger.error(f"Input file not found: {ABLATION_TRAIN_LABELS_PATH}")
            logger.error("T008 (Generate Ground Truth Labels) must run successfully before T008c.")
            return 1

        # Load the ablation labels
        labels = load_ablation_labels(ABLATION_TRAIN_LABELS_PATH)
        n = len(labels)
        
        logger.info(f"Loaded {n} records from {ABLATION_TRAIN_LABELS_PATH}")

        # Threshold defined in task spec
        THRESHOLD = 300

        if n < THRESHOLD:
            # Action 1: Log warning
            warning_msg = f"Warning: statistical power is marginal (n={n}); recommend expanding the dataset"
            log_warning(warning_msg)

            # Action 2: Generate fallback flag (true)
            flag_data = {
                "fallback": True,
                "use_heuristic": True,
                "reason": "n < 300"
            }
            write_fallback_flag(flag_data, FALLBACK_FLAG_PATH)
            logger.info(f"Sample size {n} is below threshold {THRESHOLD}. Fallback flag set to TRUE.")
        else:
            # Action 2: Generate fallback flag (false)
            flag_data = {
                "fallback": False,
                "use_heuristic": False
            }
            write_fallback_flag(flag_data, FALLBACK_FLAG_PATH)
            logger.info(f"Sample size {n} meets threshold {THRESHOLD}. Fallback flag set to FALSE.")

        return 0

    except Exception as e:
        logger.error(f"Critical error during sample size check: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())