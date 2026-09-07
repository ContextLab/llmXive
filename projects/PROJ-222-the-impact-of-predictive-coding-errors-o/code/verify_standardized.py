"""
T017: Standardized CSV Verification.

Implements verification of data/processed/standardized.csv:
1. Asserts all required columns exist (including sequence_length, stimulus_modality).
2. Asserts >= 100 valid rows.
3. Logs success/failure to analysis/verification_log.json.
"""
import json
import logging
import sys
import os
from pathlib import Path
from typing import List, Dict, Any

# Import config utilities from existing API
try:
    from config import get_data_dir, get_processed_dir
except ImportError:
    # Fallback if config is not in path (though it should be)
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_data_dir, get_processed_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('analysis/verification_log.log')
    ]
)
logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    'duration_estimate',
    'stimulus_sequence',
    'participant_id',
    'surprisal',
    'sequence_length',
    'stimulus_modality'
]

MIN_ROWS = 100

def load_standardized_csv(processed_dir: Path) -> 'pd.DataFrame':
    """Load the standardized CSV file."""
    import pandas as pd
    file_path = processed_dir / "standardized.csv"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Standardized CSV not found at {file_path}")
    
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        logger.error(f"Failed to load standardized CSV: {e}")
        raise

def verify_columns(df: 'pd.DataFrame') -> tuple[bool, List[str]]:
    """Verify all required columns are present."""
    missing = []
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            missing.append(col)
    
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False, missing
    
    logger.info(f"All required columns present: {REQUIRED_COLUMNS}")
    return True, []

def verify_row_count(df: 'pd.DataFrame') -> tuple[bool, int]:
    """Verify the dataframe has at least MIN_ROWS valid rows."""
    count = len(df)
    if count < MIN_ROWS:
        logger.error(f"Row count {count} is less than minimum {MIN_ROWS}")
        return False, count
    
    logger.info(f"Row count {count} meets minimum requirement ({MIN_ROWS})")
    return True, count

def write_verification_log(
    success: bool,
    details: Dict[str, Any],
    log_path: Path
) -> None:
    """Write the verification result to the log file."""
    log_entry = {
        "task_id": "T017",
        "timestamp": details.get("timestamp", ""),
        "success": success,
        "details": details
    }
    
    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing log if present to append, or create new
    existing_logs = []
    if log_path.exists():
        try:
            with open(log_path, 'r') as f:
                content = f.read().strip()
                if content:
                    # Handle JSONL format (one JSON per line) or list of objects
                    if content.startswith('['):
                        existing_logs = json.loads(content)
                    else:
                        # JSONL
                        for line in content.split('\n'):
                            if line.strip():
                                existing_logs.append(json.loads(line))
        except json.JSONDecodeError:
            logger.warning("Existing log file is corrupted, overwriting.")
            existing_logs = []
    
    existing_logs.append(log_entry)
    
    with open(log_path, 'w') as f:
        json.dump(existing_logs, f, indent=2)
    
    logger.info(f"Verification log written to {log_path}")

def run_verification() -> bool:
    """Main verification logic."""
    import pandas as pd
    import json
    from datetime import datetime

    processed_dir = get_processed_dir()
    analysis_dir = Path("analysis")
    log_path = analysis_dir / "verification_log.json"

    timestamp = datetime.now().isoformat()
    details = {"timestamp": timestamp, "checks": {}}

    try:
        # 1. Load Data
        logger.info(f"Loading standardized CSV from {processed_dir / 'standardized.csv'}")
        df = load_standardized_csv(processed_dir)
        details["checks"]["load"] = "passed"

        # 2. Verify Columns
        cols_ok, missing_cols = verify_columns(df)
        details["checks"]["columns"] = {
            "passed": cols_ok,
            "missing": missing_cols
        }

        # 3. Verify Row Count
        rows_ok, row_count = verify_row_count(df)
        details["checks"]["row_count"] = {
            "passed": rows_ok,
            "count": row_count,
            "min_required": MIN_ROWS
        }

        # Determine overall success
        success = cols_ok and rows_ok
        details["overall_success"] = success

        if success:
            logger.info("T017 Verification PASSED: All checks successful.")
        else:
            logger.error("T017 Verification FAILED: One or more checks failed.")

        # Write Log
        write_verification_log(success, details, log_path)

        return success

    except FileNotFoundError as e:
        logger.error(f"Critical Failure: {e}")
        details["error"] = str(e)
        details["overall_success"] = False
        write_verification_log(False, details, log_path)
        return False
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        details["error"] = str(e)
        details["overall_success"] = False
        write_verification_log(False, details, log_path)
        return False

def main():
    """Entry point."""
    success = run_verification()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
