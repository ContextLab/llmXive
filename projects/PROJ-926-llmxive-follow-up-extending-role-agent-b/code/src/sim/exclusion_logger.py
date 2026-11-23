import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.config.config import DATA_PATH

# Global exclusion log storage
_exclusion_log: List[Dict[str, Any]] = []
_exclusion_path: Optional[str] = None

def set_exclusion_path(path: str) -> None:
    """Set the path for the exclusion log file."""
    global _exclusion_path
    _exclusion_path = path
    # Ensure directory exists
    if _exclusion_path:
        os.makedirs(os.path.dirname(_exclusion_path), exist_ok=True)

def log_excluded_trajectory(trajectory_id: str, ambiguity_reason: str, timestamp: Optional[str] = None) -> Dict[str, Any]:
    """
    Log an excluded trajectory due to ambiguity.
    
    Args:
        trajectory_id: ID of the excluded trajectory
        ambiguity_reason: Reason for exclusion
        timestamp: Optional timestamp (defaults to current time)
    
    Returns:
        The logged entry
    """
    if timestamp is None:
        timestamp = datetime.now().isoformat()
    
    entry = {
        'trajectory_id': trajectory_id,
        'ambiguity_reason': ambiguity_reason,
        'timestamp': timestamp
    }
    
    _exclusion_log.append(entry)
    
    # Write to file if path is set
    if _exclusion_path:
        with open(_exclusion_path, 'w') as f:
            json.dump(_exclusion_log, f, indent=2)
    
    return entry

def log_excluded_trajectories(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Log multiple excluded trajectories.
    
    Args:
        entries: List of exclusion entries to log
    
    Returns:
        The logged entries
    """
    for entry in entries:
        _exclusion_log.append(entry)
    
    # Write to file if path is set
    if _exclusion_path:
        with open(_exclusion_path, 'w') as f:
            json.dump(_exclusion_log, f, indent=2)
    
    return entries

def get_exclusion_log() -> List[Dict[str, Any]]:
    """Get the current exclusion log."""
    return _exclusion_log.copy()

def clear_exclusion_log() -> None:
    """Clear the exclusion log."""
    global _exclusion_log
    _exclusion_log = []

def run():
    """
    Main entry point for exclusion logger (for testing).
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Test exclusion logger')
    parser.add_argument('--path', default=os.path.join(DATA_PATH, 'raw', 'excluded_log.json'),
                      help='Path to exclusion log file')
    parser.add_argument('--test', action='store_true', help='Run test mode')
    
    args = parser.parse_args()
    
    set_exclusion_path(args.path)
    
    if args.test:
        # Test logging
        test_entry = log_excluded_trajectory(
            trajectory_id="test-trajectory-001",
            ambiguity_reason="Multiple failure causes at step 5",
            timestamp=datetime.now().isoformat()
        )
        print(f"Test entry logged: {test_entry}")
        print(f"Exclusion log path: {args.path}")
        print(f"Exclusion log contents: {get_exclusion_log()}")

if __name__ == '__main__':
    run()
