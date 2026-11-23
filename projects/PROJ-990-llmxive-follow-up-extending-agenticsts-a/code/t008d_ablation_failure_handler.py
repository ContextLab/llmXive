import os
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

# Configure logging to match project standards
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/edge_case_warnings.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Constants
ABLATION_LABELS_PATH = Path("data/processed/ablation_labels_train.json")
FALLBACK_FLAG_PATH = Path("data/processed/fallback_flag.json")
EDGE_CASE_LOG_PATH = Path("data/processed/edge_case_warnings.log")

def setup_logging():
    """Ensure logging is configured for the module."""
    # Already configured in main block, but safe to call if needed
    pass

def check_ablation_success():
    """
    Check if the ablation study (T008) successfully generated labels.
    Returns True if the file exists and contains valid JSON data.
    Returns False if the file is missing, empty, or invalid.
    """
    if not ABLATION_LABELS_PATH.exists():
        logger.warning(f"Ablation labels file not found at {ABLATION_LABELS_PATH}")
        return False

    try:
        with open(ABLATION_LABELS_PATH, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                logger.warning(f"Ablation labels file is empty: {ABLATION_LABELS_PATH}")
                return False
            
            data = json.loads(content)
            # Basic validation: ensure it's a dict or list with content
            if isinstance(data, (dict, list)) and len(data) > 0:
                return True
            else:
                logger.warning(f"Ablation labels file contains no data entries: {ABLATION_LABELS_PATH}")
                return False
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in ablation labels file: {e}")
        return False
    except Exception as e:
        logger.error(f"Error reading ablation labels file: {e}")
        return False

def log_critical_failure(reason: str):
    """
    Log a CRITICAL error to the edge case warnings log.
    """
    timestamp = datetime.utcnow().isoformat()
    message = f"[CRITICAL] Ablation study failed at {timestamp}. Reason: {reason}. Pipeline switching to fallback heuristic."
    logger.critical(message)
    
    # Ensure the log file exists and append the message
    EDGE_CASE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(EDGE_CASE_LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(message + "\n")

def generate_fallback_flag(reason: str):
    """
    Generate the fallback_flag.json file indicating the pipeline must use heuristics.
    """
    fallback_data = {
        "fallback": True,
        "use_heuristic": True,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat(),
        "heuristic_params": {
            "k": 2,
            "selection_mode": "fixed_k_random"
        }
    }
    
    FALLBACK_FLAG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(FALLBACK_FLAG_PATH, 'w', encoding='utf-8') as f:
        json.dump(fallback_data, f, indent=2)
    
    logger.info(f"Fallback flag generated at {FALLBACK_FLAG_PATH}")

def main():
    """
    Main entry point for T008d: Ablation Failure Handling.
    
    Logic:
    1. Check if T008 (ablation study) succeeded by verifying existence and validity of ablation_labels_train.json.
    2. If T008 FAILED (file missing, empty, or invalid):
       - Log a CRITICAL error to data/processed/edge_case_warnings.log.
       - Generate data/processed/fallback_flag.json with fallback=true, use_heuristic=true.
       - Do NOT generate mock data.
    3. If T008 SUCCEEDED:
       - Log an info message that no fallback is needed.
       - Do NOT generate fallback_flag.json.
    """
    logger.info("Starting T008d: Ablation Failure Handling check.")
    
    # Check if ablation study was successful
    ablation_success = check_ablation_success()
    
    if not ablation_success:
        # T008 Failed: Trigger fallback handling
        reason = "Ablation study failed to generate valid labels"
        log_critical_failure(reason)
        generate_fallback_flag(reason)
        logger.warning("T008d completed: Fallback flag generated. Pipeline must switch to heuristic (k=2).")
    else:
        # T008 Succeeded: No action needed
        logger.info("Ablation study succeeded. No fallback required.")
        # Ensure we don't leave a stale fallback flag if it existed from a previous run
        # (Optional cleanup, but safer to leave it to the pipeline logic to check the flag's existence)
        logger.info("T008d completed: No failure detected.")

if __name__ == "__main__":
    main()
