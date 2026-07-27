"""
T008c: Sample Count Check and Fallback Flag Generator.

Logic:
1. Count rows in data/processed/ablation_labels_train.json (from T008).
2. If n < 300:
   - Log warning to data/processed/edge_case_warnings.log.
   - Write data/processed/fallback_flag.json with fallback=true.
3. Else:
   - Write data/processed/fallback_flag.json with fallback=false.

Dependencies:
- T008 (ablation_labels_train.json)
"""
import json
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
ABALATION_LABELS_PATH = PROCESSED_DIR / "ablation_labels_train.json"
FALLBACK_FLAG_PATH = PROCESSED_DIR / "fallback_flag.json"
WARNINGS_LOG_PATH = PROCESSED_DIR / "edge_case_warnings.log"

SAMPLE_THRESHOLD = 300

def load_ablation_labels(path: Path) -> list:
    """Load ablation labels from JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list and dict structures if necessary, though spec implies list of records
    if isinstance(data, dict):
        # If it's a dict of records, extract values
        return list(data.values())
    return data

def log_warning(message: str, log_path: Path) -> None:
    """Append a warning message to the edge case warnings log."""
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(message + "\n")
    logger.warning(message)

def write_fallback_flag(is_fallback: bool, reason: str, path: Path) -> None:
    """Write the fallback flag JSON."""
    report = {
        "fallback": is_fallback,
        "reason": reason if is_fallback else None
    }
    # Remove None values for cleaner JSON if needed, but spec shows explicit reason
    if not is_fallback:
        report = {"fallback": False}
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Fallback flag written to {path}: {report}")

def main():
    """Main execution for T008c."""
    logger.info(f"Starting T008c: Sample Count Check")
    logger.info(f"Input: {ABALATION_LABELS_PATH}")

    # 1. Verify input exists
    if not ABALATION_LABELS_PATH.exists():
        raise FileNotFoundError(
            f"Input file missing: {ABALATION_LABELS_PATH}. "
            "Ensure T008 (Generate Ground Truth Labels) has completed successfully."
        )

    # 2. Load and count rows
    try:
        labels = load_ablation_labels(ABALATION_LABELS_PATH)
        n = len(labels)
        logger.info(f"Loaded {n} records from ablation labels.")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        raise

    # 3. Check threshold and act
    if n < SAMPLE_THRESHOLD:
        warning_msg = f"Warning: statistical power is marginal (n={n}); recommend expanding the dataset"
        log_warning(warning_msg, WARNINGS_LOG_PATH)
        write_fallback_flag(True, "n < 300", FALLBACK_FLAG_PATH)
    else:
        write_fallback_flag(False, "", FALLBACK_FLAG_PATH)

    logger.info("T008c completed successfully.")

if __name__ == "__main__":
    main()