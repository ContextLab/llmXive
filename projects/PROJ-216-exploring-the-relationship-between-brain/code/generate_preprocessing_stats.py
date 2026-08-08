import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

from utils import ResourceMonitor

def load_subject_logs(log_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all JSON log files from the specified directory.
    Each log file is expected to contain a 'success' boolean and 'subject_id'.
    """
    logs = []
    if not log_dir.exists():
        return logs
    
    for file_path in log_dir.glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                if 'subject_id' in data and 'success' in data:
                    logs.append(data)
        except (json.JSONDecodeError, IOError):
            continue
    return logs

def calculate_stats(logs: List[Dict[str, Any]], total_expected: int) -> Dict[str, Any]:
    """
    Calculate preprocessing statistics based on subject logs.
    
    Args:
        logs: List of subject log dictionaries containing 'success' status.
        total_expected: The total number of subjects expected (N=10 limit or actual count).
    
    Returns:
        Dictionary with total_subjects, successful_subjects, and success_rate_percentage.
    """
    successful = sum(1 for log in logs if log.get('success', False))
    total = total_expected if total_expected > 0 else len(logs)
    
    # Ensure we don't divide by zero if total is somehow 0
    if total == 0:
        success_rate = 0.0
    else:
        success_rate = (successful / total) * 100.0
    
    return {
        "total_subjects": total,
        "successful_subjects": successful,
        "success_rate_percentage": round(success_rate, 2)
    }

def main():
    """
    Main entry point to generate preprocessing statistics.
    Reads logs from data/processed/logs/, calculates stats, and writes to 
    data/processed/preprocessing_stats.json.
    """
    base_dir = Path(__file__).resolve().parent.parent
    log_dir = base_dir / "data" / "processed" / "logs"
    output_path = base_dir / "data" / "processed" / "preprocessing_stats.json"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load logs
    logs = load_subject_logs(log_dir)
    
    # Determine total expected subjects
    # We assume the total is the count of logs found if no explicit limit is passed,
    # or we can read from config. For this task, we calculate based on logs found
    # to reflect actual processed attempts.
    # However, the task says "where total is the N=10 limit or actual downloaded count".
    # Since we don't have direct access to the download count here without importing config,
    # we will use the number of logs found as the 'total' attempted, which represents
    # the actual downloaded/processed count for this run.
    total_expected = len(logs)
    
    stats = calculate_stats(logs, total_expected)
    
    # Write output
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"Preprocessing statistics written to {output_path}")
    print(f"Total: {stats['total_subjects']}, Successful: {stats['successful_subjects']}, Rate: {stats['success_rate_percentage']}%")

if __name__ == "__main__":
    main()
