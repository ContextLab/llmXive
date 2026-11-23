import json
import os
from pathlib import Path
from typing import Dict, Any, Tuple
from utils.config import get_path

def load_execution_log(log_path: Path) -> list:
    """Load an execution log file."""
    entries = []
    if log_path.exists():
        with open(log_path, 'r') as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
    return entries

def count_outcomes(entries: list) -> Dict[str, int]:
    """Count success and failure outcomes."""
    counts = {'success': 0, 'failure': 0}
    for entry in entries:
        status = entry.get('status', 'unknown')
        if status in counts:
            counts[status] += 1
        else:
            counts['failure'] += 1
    return counts

def parse_baseline_log(log_path: Path) -> Dict[str, Any]:
    """Parse baseline execution log."""
    entries = load_execution_log(log_path)
    counts = count_outcomes(entries)
    return {
        'total': len(entries),
        'success': counts['success'],
        'failure': counts['failure'],
        'success_rate': counts['success'] / len(entries) if entries else 0.0
    }

def parse_augmented_log(log_path: Path) -> Dict[str, Any]:
    """Parse augmented execution log."""
    entries = load_execution_log(log_path)
    counts = count_outcomes(entries)
    recovery_count = sum(1 for e in entries if e.get('recovery_strategy'))
    return {
        'total': len(entries),
        'success': counts['success'],
        'failure': counts['failure'],
        'success_rate': counts['success'] / len(entries) if entries else 0.0,
        'recovery_attempts': recovery_count
    }

def get_aggregated_counts(baseline_path: Path, augmented_path: Path) -> Tuple[Dict[str, int], Dict[str, int]]:
    """Get aggregated success/failure counts for both agents."""
    baseline_stats = parse_baseline_log(baseline_path)
    augmented_stats = parse_augmented_log(augmented_path)
    
    baseline_counts = {
        'success': baseline_stats['success'],
        'failure': baseline_stats['failure']
    }
    augmented_counts = {
        'success': augmented_stats['success'],
        'failure': augmented_stats['failure']
    }
    
    return baseline_counts, augmented_counts

def main():
    """Main entry point for log parser."""
    baseline_path = get_path('data/logs/baseline_execution.jsonl')
    augmented_path = get_path('data/logs/augmented_execution.jsonl')
    
    baseline_stats = parse_baseline_log(baseline_path)
    augmented_stats = parse_augmented_log(augmented_path)
    
    print(f"Baseline: {baseline_stats}")
    print(f"Augmented: {augmented_stats}")

if __name__ == "__main__":
    main()
