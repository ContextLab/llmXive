import os
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

# Ensure we can import sibling modules
sys.path.insert(0, str(Path(__file__).parent))

def setup_logging():
    """Configure logging to output to file and console."""
    log_dir = Path("data/processed")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "edge_case_warnings.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, mode='a'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def check_ablation_success(ablation_labels_path: str) -> bool:
    """
    Check if the ablation study succeeded by verifying the output file exists
    and contains valid data (non-empty list/dict).
    """
    path = Path(ablation_labels_path)
    if not path.exists():
        return False
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        
        # If it's a dict, check if it's empty. If it's a list, check if it's empty.
        if isinstance(data, dict) and len(data) == 0:
            return False
        if isinstance(data, list) and len(data) == 0:
            return False
        
        return True
    except (json.JSONDecodeError, IOError):
        return False

def log_critical_failure(logger: logging.Logger, reason: str):
    """
    Log a CRITICAL error to the edge_case_warnings.log file.
    """
    timestamp = datetime.now().isoformat()
    message = f"CRITICAL: Ablation study failed at {timestamp}. Reason: {reason}"
    logger.critical(message)

def generate_fallback_flag(output_path: str, reason: str):
    """
    Generate the fallback_flag.json file indicating the pipeline must switch
    to the fixed-k heuristic (k=2) because the ablation study failed.
    """
    flag_data = {
        "fallback": True,
        "use_heuristic": True,
        "reason": reason,
        "timestamp": datetime.now().isoformat()
    }
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(flag_data, f, indent=2)
    
    return output_file

def main():
    """
    Main entry point for T008d: Ablation Failure Handling.
    
    Logic:
    1. Check if T008 (ablation study) produced valid output.
    2. If T008 failed (file missing or empty), log CRITICAL error and generate fallback_flag.json.
    3. If T008 succeeded, log info and exit (no action needed).
    
    This script is designed to be run conditionally after T008.
    """
    logger = setup_logging()
    
    ablation_labels_path = "data/processed/ablation_labels_train.json"
    fallback_flag_path = "data/processed/fallback_flag.json"
    
    logger.info(f"Checking ablation success status for: {ablation_labels_path}")
    
    if check_ablation_success(ablation_labels_path):
        logger.info("Ablation study succeeded. No fallback action required.")
        return
    
    # Ablation study failed (file missing, empty, or invalid)
    reason = "Ablation study failed to generate valid labels (missing or empty output)."
    log_critical_failure(logger, reason)
    generate_fallback_flag(fallback_flag_path, reason)
    
    logger.info(f"Fallback flag generated at: {fallback_flag_path}")
    logger.info("Pipeline must now switch to fixed-k heuristic (k=2) for training.")
    # Note: We do NOT exit with error code here to allow the pipeline to 
    # potentially continue with the fallback path, but the flag indicates failure.

if __name__ == "__main__":
    main()
