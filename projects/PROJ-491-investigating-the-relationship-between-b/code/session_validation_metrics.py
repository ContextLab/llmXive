import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any

# Import from existing project modules as per API surface
from config import ensure_directories
from write_excluded_session_ids import load_validation_state

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_pass_rate(total_subjects: int, excluded_count: int) -> float:
    """
    Calculate the pass-rate percentage of subjects with distinct session IDs.
    
    Args:
        total_subjects: Total number of subjects attempted.
        excluded_count: Number of subjects excluded due to session ID mismatch.
    
    Returns:
        Pass rate as a percentage (0.0 to 100.0).
    """
    if total_subjects == 0:
        return 0.0
    valid_count = total_subjects - excluded_count
    return (valid_count / total_subjects) * 100.0

def write_metrics(metrics: Dict[str, Any], output_path: Path) -> None:
    """
    Write the session validation metrics to a JSON file.
    
    Args:
        metrics: Dictionary containing the metrics.
        output_path: Path to the output JSON file.
    """
    ensure_directories([output_path.parent])
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics written to {output_path}")

def main() -> int:
    """
    Main entry point for calculating and writing session validation metrics.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        # Ensure output directory exists
        metrics_path = Path("data/processed/session_validation_metrics.json")
        
        # Load validation state to get counts
        # This function is defined in write_excluded_session_ids.py
        validation_data = load_validation_state()
        
        if not validation_data:
            logger.error("No validation state found. Run data ingestion and session validation first.")
            return 1
        
        total_subjects = validation_data.get('total_subjects', 0)
        excluded_subjects = validation_data.get('excluded_subjects', [])
        excluded_count = len(excluded_subjects)
        
        pass_rate = calculate_pass_rate(total_subjects, excluded_count)
        
        metrics = {
            "total_subjects": total_subjects,
            "excluded_subjects_count": excluded_count,
            "valid_subjects_count": total_subjects - excluded_count,
            "pass_rate_percentage": round(pass_rate, 2),
            "validation_timestamp": validation_data.get('timestamp', 'unknown')
        }
        
        write_metrics(metrics, metrics_path)
        
        logger.info(f"Session validation complete: {pass_rate:.2f}% pass rate ({total_subjects - excluded_count}/{total_subjects} subjects)")
        return 0
        
    except Exception as e:
        logger.error(f"Failed to calculate session validation metrics: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
