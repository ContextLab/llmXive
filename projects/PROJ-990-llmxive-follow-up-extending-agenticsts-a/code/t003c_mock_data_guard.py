import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dev_mode() -> bool:
    """
    Check if DEV_MODE environment variable is set and truthy.
    Returns True if in DEV_MODE, False otherwise.
    """
    dev_mode = os.environ.get("DEV_MODE", "").strip().lower()
    return dev_mode in ("1", "true", "yes", "on")

def is_file_empty(file_path: Path) -> bool:
    """
    Check if a file exists and is empty.
    Returns True if file does not exist or is empty.
    """
    if not file_path.exists():
        return True
    if file_path.stat().st_size == 0:
        return True
    return False

def run_guard_check() -> Dict[str, Any]:
    """
    Execute the mock data guard logic.
    
    Logic:
    1. Check DEV_MODE.
    2. If DEV_MODE is NOT set (production):
       - Verify data/fixtures/mock_trajectories.jsonl is NOT present or is empty.
       - If mock data exists and is non-empty, raise RuntimeError.
    3. If DEV_MODE IS set (development):
       - Allow mock data to exist (it is expected).
    
    Returns:
        Dict with status ("passed" or "blocked") and metadata.
    """
    mock_data_path = Path("data/fixtures/mock_trajectories.jsonl")
    output_path = Path("data/processed/dev_mode_guard.json")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    in_dev_mode = check_dev_mode()
    logger.info(f"DEV_MODE status: {'ENABLED' if in_dev_mode else 'DISABLED (Production)'}")
    
    status = "passed"
    message = "Guard check passed."
    
    if not in_dev_mode:
        # Production Mode: Mock data must not exist or must be empty
        if mock_data_path.exists():
            if not is_file_empty(mock_data_path):
                error_msg = "Mock data detected in production run; aborting."
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            else:
                logger.info("Mock data file exists but is empty. OK.")
        else:
            logger.info("Mock data file does not exist. OK.")
    else:
        # Development Mode: Mock data is allowed
        if mock_data_path.exists() and not is_file_empty(mock_data_path):
            logger.info("Development mode active. Mock data detected and allowed.")
        elif not mock_data_path.exists():
            logger.warning("Development mode active, but mock data file is missing. "
                         "Ensure T003b has run if you intend to use mock data.")
        
    result = {
        "status": status,
        "message": message,
        "dev_mode": in_dev_mode,
        "mock_data_path": str(mock_data_path),
        "mock_data_exists": mock_data_path.exists(),
        "mock_data_empty": is_file_empty(mock_data_path) if mock_data_path.exists() else True,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    # Write result to disk
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Guard check result written to {output_path}")
    return result

def save_report(result: Dict[str, Any]) -> None:
    """
    Save the guard check result to the specified output path.
    (Wrapper for explicit reporting, though run_guard_check already saves).
    """
    output_path = Path("data/processed/dev_mode_guard.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

def main():
    """
    Entry point for T003c: Enforce Mock Data Guard.
    """
    try:
        result = run_guard_check()
        logger.info("T003c Mock Data Guard completed successfully.")
    except RuntimeError as e:
        logger.error(f"T003c Mock Data Guard failed: {e}")
        # Re-raise to ensure the pipeline stops as per constraint
        raise
    except Exception as e:
        logger.error(f"Unexpected error in T003c: {e}")
        raise

if __name__ == "__main__":
    main()
