"""
Log parser for analyzing execution logs from baseline and augmented agents.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Tuple

from utils.config import get_path

def load_execution_log(log_path: Path) -> list:
    """
    Load a JSONL execution log file.
    
    Args:
        log_path: Path to the JSONL file.
        
    Returns:
        List of log entries as dictionaries.
        
    Raises:
        FileNotFoundError: If the log file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    if not log_path.exists():
        raise FileNotFoundError(f"Log file not found: {log_path}")
    
    entries = []
    with open(log_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(
                    f"Invalid JSON at line {line_num} in {log_path}: {e.msg}",
                    e.doc, e.pos
                )
    return entries

def count_outcomes(entries: list) -> Dict[str, int]:
    """
    Count success and failure outcomes from log entries.
    
    Args:
        entries: List of log entries.
        
    Returns:
        Dictionary with 'success' and 'failure' counts.
    """
    counts = {'success': 0, 'failure': 0}
    for entry in entries:
        status = entry.get('status', '').lower()
        if status == 'success':
            counts['success'] += 1
        elif status == 'failure':
            counts['failure'] += 1
        # Ignore entries with unknown status
    return counts

def parse_baseline_log(log_path: Path = None) -> Tuple[int, int]:
    """
    Parse the baseline execution log and return success/failure counts.
    
    Args:
        log_path: Optional override for log path. Defaults to config.
        
    Returns:
        Tuple of (success_count, failure_count)
    """
    if log_path is None:
        log_path = get_path('baseline_log')
    
    entries = load_execution_log(log_path)
    counts = count_outcomes(entries)
    return counts['success'], counts['failure']

def parse_augmented_log(log_path: Path = None) -> Tuple[int, int]:
    """
    Parse the augmented execution log and return success/failure counts.
    
    Args:
        log_path: Optional override for log path. Defaults to config.
        
    Returns:
        Tuple of (success_count, failure_count)
    """
    if log_path is None:
        log_path = get_path('augmented_log')
    
    entries = load_execution_log(log_path)
    counts = count_outcomes(entries)
    return counts['success'], counts['failure']

def get_aggregated_counts() -> Dict[str, Tuple[int, int]]:
    """
    Get aggregated success/failure counts for both baseline and augmented logs.
    
    Returns:
        Dictionary with keys 'baseline' and 'augmented', each containing
        a tuple of (success_count, failure_count).
    """
    baseline_path = get_path('baseline_log')
    augmented_path = get_path('augmented_log')
    
    return {
        'baseline': parse_baseline_log(baseline_path),
        'augmented': parse_augmented_log(augmented_path)
    }

def main():
    """
    Main entry point for log parsing. Prints aggregated counts.
    """
    try:
        counts = get_aggregated_counts()
        print("Aggregated Execution Counts:")
        print(f"  Baseline: Success={counts['baseline'][0]}, Failure={counts['baseline'][1]}")
        print(f"  Augmented: Success={counts['augmented'][0]}, Failure={counts['augmented'][1]}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return 1
    return 0

if __name__ == '__main__':
    exit(main())
