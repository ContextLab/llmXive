"""
T034: Implement logic to flag "latency-induced failures" (>150ms) in TaskOutcome records.

This module reads evaluation outcomes, checks the associated perception latency
from the PerceptionLog, and flags tasks where latency exceeded the 150ms threshold
as 'latency-induced failures'.

Output: Updates the 'failure_category' field in TaskOutcome records to 'latency'
        if the latency threshold is exceeded and the task failed.
"""
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import get_path, get_hyperparameter
from utils.exceptions import LlmXiveError
from data.models import TaskOutcome, FailureType


LATENCY_THRESHOLD_MS = 150.0  # FR-008, T034 threshold


def load_task_outcomes(outcome_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load task outcomes from the evaluation output file."""
    if outcome_path is None:
        outcome_path = get_path("data", "processed", "evaluation_outcomes.json")
    
    if not os.path.exists(outcome_path):
        raise LlmXiveError(f"Task outcomes file not found at {outcome_path}. "
                           "Run evaluation first (T031-T032).")
    
    with open(outcome_path, 'r') as f:
        data = json.load(f)
    
    # Handle both list format and dict with 'outcomes' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'outcomes' in data:
        return data['outcomes']
    else:
        raise LlmXiveError("Invalid task outcomes format. Expected list or dict with 'outcomes' key.")


def load_perception_log(log_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the perception log containing latency measurements."""
    if log_path is None:
        log_path = get_path("data", "artifacts", "perception_log.json")
    
    if not os.path.exists(log_path):
        raise LlmXiveError(f"Perception log not found at {log_path}. "
                           "Run perception transformation first (T016).")
    
    with open(outcome_path, 'r') as f:
        return json.load(f)


def get_latency_for_task(perception_log: Dict[str, Any], task_id: str) -> Optional[float]:
    """
    Retrieve the average perception latency for a specific task.
    
    The perception log is structured as a list of entries, each containing
    a task_id and latency measurements.
    """
    # Handle different log structures
    if 'entries' in perception_log:
        entries = perception_log['entries']
    elif isinstance(perception_log, list):
        entries = perception_log
    else:
        # Assume single entry or flat structure
        entries = [perception_log]
    
    for entry in entries:
        if entry.get('task_id') == task_id:
            # Return average latency if available
            if 'avg_latency_ms' in entry:
                return entry['avg_latency_ms']
            elif 'latency_ms' in entry:
                return entry['latency_ms']
            elif 'latencies' in entry and isinstance(entry['latencies'], list):
                return sum(entry['latencies']) / len(entry['latencies'])
    
    return None


def flag_latency_induced_failures(
    outcomes: List[Dict[str, Any]], 
    perception_log: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Flag tasks as latency-induced failures if latency > 150ms and task failed.
    
    Updates the 'failure_category' field to 'latency' for affected tasks.
    """
    flagged_count = 0
    
    for outcome in outcomes:
        task_id = outcome.get('task_id')
        if not task_id:
            continue
        
        # Only process failed tasks
        is_success = outcome.get('success', False)
        if is_success:
            continue
        
        # Get latency for this task
        latency = get_latency_for_task(perception_log, task_id)
        
        if latency is None:
            # No latency data found, skip or log warning
            continue
        
        # Check if latency exceeds threshold
        if latency > LATENCY_THRESHOLD_MS:
            outcome['failure_category'] = 'latency'
            outcome['latency_ms'] = latency
            outcome['latency_threshold_ms'] = LATENCY_THRESHOLD_MS
            outcome['is_latency_induced_failure'] = True
            flagged_count += 1
        else:
            outcome['is_latency_induced_failure'] = False
    
    return outcomes


def write_flagged_outcomes(
    outcomes: List[Dict[str, Any]], 
    output_path: Optional[Path] = None
) -> Path:
    """Write the updated outcomes to the output file."""
    if output_path is None:
        output_path = get_path("data", "processed", "evaluation_outcomes.json")
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(outcomes, f, indent=2, default=str)
    
    return output_path


def main():
    """Main entry point for T034: Flag latency-induced failures."""
    print("T034: Flagging latency-induced failures...")
    
    try:
        # Load data
        outcomes = load_task_outcomes()
        perception_log = load_perception_log()
        
        print(f"Loaded {len(outcomes)} task outcomes")
        print(f"Perception log loaded successfully")
        
        # Flag failures
        updated_outcomes = flag_latency_induced_failures(outcomes, perception_log)
        
        # Count flagged failures
        flagged = sum(1 for o in updated_outcomes if o.get('is_latency_induced_failure', False))
        print(f"Flagged {flagged} latency-induced failures (latency > {LATENCY_THRESHOLD_MS}ms)")
        
        # Write results
        output_path = write_flagged_outcomes(updated_outcomes)
        print(f"Updated outcomes written to {output_path}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()