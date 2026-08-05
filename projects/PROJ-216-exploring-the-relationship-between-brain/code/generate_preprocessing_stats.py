import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

from utils import ResourceMonitor

def load_subject_logs(log_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all subject preprocessing logs from the specified directory.
    Expects JSON files named <subject_id>_preprocess_log.json.
    """
    if not log_dir.exists():
        return []
    
    logs = []
    for log_file in log_dir.glob("*_preprocess_log.json"):
        try:
            with open(log_file, 'r') as f:
                data = json.load(f)
                # Ensure the log indicates success
                if data.get('status') == 'success':
                    logs.append({
                        'subject_id': data.get('subject_id', log_file.stem.replace('_preprocess_log', '')),
                        'success': True,
                        'metrics': data.get('metrics', {})
                    })
                elif data.get('status') == 'failed':
                    logs.append({
                        'subject_id': data.get('subject_id', log_file.stem.replace('_preprocess_log', '')),
                        'success': False,
                        'reason': data.get('reason', 'Unknown error')
                    })
        except (json.JSONDecodeError, IOError):
            # Skip malformed logs
            continue
    return logs

def calculate_stats(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate preprocessing statistics from the list of subject logs.
    Returns a dict with total_subjects, successful_subjects, and success_rate_percentage.
    """
    total = len(logs)
    successful = sum(1 for log in logs if log.get('success', False))
    
    rate = 0.0
    if total > 0:
        rate = (successful / total) * 100.0
    
    return {
        'total_subjects': total,
        'successful_subjects': successful,
        'success_rate_percentage': round(rate, 2)
    }

def main():
    """
    Main entry point to generate preprocessing statistics.
    Reads logs from data/processed/logs/ (or similar) and writes
    data/processed/preprocessing_stats.json.
    """
    # Determine paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    log_dir = project_root / 'data' / 'processed' / 'logs'
    output_path = project_root / 'data' / 'processed' / 'preprocessing_stats.json'
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load logs
    logs = load_subject_logs(log_dir)
    
    if not logs:
        # If no logs found, check if there's a fallback or error condition
        # For now, we assume 0 total if no logs are found in the expected location
        stats = {
            'total_subjects': 0,
            'successful_subjects': 0,
            'success_rate_percentage': 0.0
        }
        print(f"Warning: No preprocessing logs found in {log_dir}. Stats set to 0.")
    else:
        stats = calculate_stats(logs)
    
    # Write output
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"Preprocessing statistics written to {output_path}")
    print(f"Total: {stats['total_subjects']}, Successful: {stats['successful_subjects']}, Rate: {stats['success_rate_percentage']}%")

if __name__ == '__main__':
    main()
