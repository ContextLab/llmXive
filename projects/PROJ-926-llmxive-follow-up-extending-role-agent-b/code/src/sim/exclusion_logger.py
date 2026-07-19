import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

_exclusion_path: Optional[str] = None
_exclusion_log: List[Dict[str, Any]] = []

def set_exclusion_path(path: str) -> None:
    """Set the path for the exclusion log file."""
    global _exclusion_path
    _exclusion_path = path
    # Ensure directory exists
    os.makedirs(os.path.dirname(path), exist_ok=True)

def log_excluded_trajectory(
    trajectory_id: str,
    exclusion_reason: str,
    ambiguity_reason: Optional[str] = None,
    ground_truth_snapshot_id: Optional[str] = None,
    action_log_preview: Optional[List[Dict[str, Any]]] = None
) -> None:
    """
    Log an excluded trajectory to memory and optionally to disk.
    
    Args:
        trajectory_id: Unique identifier for the trajectory
        exclusion_reason: Reason for exclusion
        ambiguity_reason: Specific reason if excluded due to ambiguity
        ground_truth_snapshot_id: ID of the ground truth snapshot
        action_log_preview: Preview of action log for debugging
    """
    entry = {
        "trajectory_id": trajectory_id,
        "exclusion_reason": exclusion_reason,
        "ambiguity_reason": ambiguity_reason,
        "ground_truth_snapshot_id": ground_truth_snapshot_id,
        "timestamp": datetime.utcnow().isoformat(),
        "action_log_preview": action_log_preview or []
    }
    
    _exclusion_log.append(entry)
    
    # Write to disk if path is set
    if _exclusion_path:
        with open(_exclusion_path, 'w', encoding='utf-8') as f:
            json.dump(_exclusion_log, f, indent=2)

def log_excluded_trajectories(entries: List[Dict[str, Any]]) -> None:
    """Log multiple excluded trajectories at once."""
    for entry in entries:
        log_excluded_trajectory(
            trajectory_id=entry.get("trajectory_id", "unknown"),
            exclusion_reason=entry.get("exclusion_reason", "unknown"),
            ambiguity_reason=entry.get("ambiguity_reason"),
            ground_truth_snapshot_id=entry.get("ground_truth_snapshot_id"),
            action_log_preview=entry.get("action_log_preview", [])
        )

def get_exclusion_log() -> List[Dict[str, Any]]:
    """Get the current exclusion log."""
    return _exclusion_log.copy()

def clear_exclusion_log() -> None:
    """Clear the exclusion log."""
    global _exclusion_log
    _exclusion_log = []

def run():
    """Main entry point for exclusion logger (for testing)."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Exclusion logger utility")
    parser.add_argument("--path", required=True, help="Path to exclusion log file")
    parser.add_argument("--test", action="store_true", help="Run test mode")
    
    args = parser.parse_args()
    
    if args.test:
        set_exclusion_path(args.path)
        log_excluded_trajectory(
            trajectory_id="test_123",
            exclusion_reason="Test exclusion",
            ambiguity_reason="test_ambiguity"
        )
        print(f"Test entry logged to {args.path}")
        print(json.dumps(_exclusion_log, indent=2))
    else:
        print("Usage: python exclusion_logger.py --path <file> --test")

if __name__ == "__main__":
    run()
