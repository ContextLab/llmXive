import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from code.config import Config
from code.utils.logging import setup_logging

logger = logging.getLogger(__name__)


def load_subject_logs(logs_dir: Path) -> List[Dict[str, Any]]:
    """
    Load subject logs from the logs directory.

    Args:
        logs_dir: Path to the logs directory.

    Returns:
        List of log entries.
    """
    logs = []
    log_file = logs_dir / "preprocessing.log"
    if not log_file.exists():
        logger.warning("Preprocessing log not found.")
        return logs
    
    # Simplified parsing of log file
    # In real implementation, parse JSON logs or structured text
    with open(log_file, 'r') as f:
        for line in f:
            if "excluded" in line.lower():
                # Extract subject ID and reason
                # Placeholder logic
                logs.append({"subject_id": "unknown", "reason": "unknown"})
    return logs


def save_subject_info(
    subject_data: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Save subject information, exclusion reasons, and motion metrics to JSON.

    Args:
        subject_data: List of dictionaries containing subject info.
        output_path: Path to save the JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(subject_data, f, indent=2)
    
    logger.info(f"Saved subject info to {output_path}")


def run_save_metadata(
    logs_dir: Path,
    output_path: Path,
    processed_results: List[Dict[str, Any]]
) -> None:
    """
    Run the metadata saving process.

    Args:
        logs_dir: Path to logs directory.
        output_path: Path to save the final JSON.
        processed_results: List of preprocessing results.
    """
    # Combine logs and processed results
    # In real implementation, merge data sources properly
    subject_info = []
    for res in processed_results:
        subject_info.append({
            "subject_id": res.get("subject_id"),
            "fd": res.get("fd"),
            "excluded": res.get("excluded"),
            "reason": res.get("reason"),
            "timestamp": datetime.now().isoformat()
        })
    
    save_subject_info(subject_info, output_path)


def main():
    """Main entry point for the save metadata script."""
    setup_logging()
    config = Config()
    
    logs_dir = Path(config.logs_dir)
    output_path = Path(config.subject_info_path)
    
    # Placeholder results
    processed_results = [
        {"subject_id": "sub-001", "fd": 0.5, "excluded": False, "reason": "Pass"},
        {"subject_id": "sub-002", "fd": 3.5, "excluded": True, "reason": "FD too high"}
    ]
    
    run_save_metadata(logs_dir, output_path, processed_results)


if __name__ == "__main__":
    main()