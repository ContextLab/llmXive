import json
import os
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from src.config.config import DATA_PATH, SEED
from src.sim.alfworld_runner import run_episode
from src.sim.exclusion_logger import log_excluded_trajectory, set_exclusion_path

# Priority rules for resolving ambiguous ground-truth causes
# Higher index = lower priority. If multiple causes match, the one with the highest priority
# (lowest index) is selected. If multiple causes share the highest priority, it's ambiguous.
PRIORITY_RULES = [
    "object_not_found",
    "navigation_failure",
    "action_sequence_error",
    "tool_usage_error",
    "timeout_exceeded"
]

def load_ground_truth_raw() -> List[Dict[str, Any]]:
    """Load the raw ground-truth data from disk."""
    gt_path = os.path.join(DATA_PATH, "raw", "ground_truth_raw.json")
    if not os.path.exists(gt_path):
        raise FileNotFoundError(f"Ground truth raw file not found: {gt_path}")
    
    with open(gt_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_trajectory(action_log: List[Dict[str, Any]], ground_truth_snapshot: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    """
    Validate a trajectory against ground truth.
    
    Returns:
        Tuple of (validation_status, reason_code)
        validation_status: 'PASS', 'FAIL', 'AMBIGUOUS', 'EXCLUDED'
        reason_code: Specific code explaining the status
    """
    # Extract potential failure causes from the action log
    potential_causes = []
    
    # Check for object not found
    if any("object not found" in step.get("observation", "").lower() for step in action_log):
        potential_causes.append("object_not_found")
    
    # Check for navigation failure
    if any("cannot navigate" in step.get("observation", "").lower() or "blocked" in step.get("observation", "").lower() for step in action_log):
        potential_causes.append("navigation_failure")
    
    # Check for action sequence error
    if any("invalid action" in step.get("observation", "").lower() or "action failed" in step.get("observation", "").lower() for step in action_log):
        potential_causes.append("action_sequence_error")
    
    # Check for tool usage error
    if any("tool" in step.get("observation", "").lower() and "failed" in step.get("observation", "").lower() for step in action_log):
        potential_causes.append("tool_usage_error")
    
    # Check for timeout
    if len(action_log) > 50:  # Arbitrary threshold for timeout
        potential_causes.append("timeout_exceeded")
    
    if not potential_causes:
        return "PASS", None
    
    # Determine priority of each cause
    cause_priorities = [(cause, PRIORITY_RULES.index(cause)) for cause in potential_causes if cause in PRIORITY_RULES]
    
    if not cause_priorities:
        # No recognized causes, mark as ambiguous
        return "AMBIGUOUS", "unrecognized_failure_pattern"
    
    # Find the minimum priority (highest priority cause)
    min_priority = min(priority for _, priority in cause_priorities)
    highest_priority_causes = [cause for cause, priority in cause_priorities if priority == min_priority]
    
    # If multiple causes share the highest priority, it's ambiguous
    if len(highest_priority_causes) > 1:
        return "AMBIGUOUS", "multiple_highest_priority_causes"
    
    # Single highest priority cause
    return "FAIL", highest_priority_causes[0]

def process_trajectory_for_ambiguity(trajectory_id: str, action_log: List[Dict[str, Any]], ground_truth_snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single trajectory to check for ambiguity and handle excluded cases.
    
    Returns:
        Dict containing validation result and exclusion info if applicable.
    """
    status, reason_code = validate_trajectory(action_log, ground_truth_snapshot)
    
    result = {
        "trajectory_id": trajectory_id,
        "validation_status": status,
        "reason_code": reason_code,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Handle ambiguous cases
    if status == "AMBIGUOUS":
        result["exclusion_status"] = "EXCLUDED"
        result["ambiguity_reason"] = reason_code
        result["ground_truth_snapshot_id"] = ground_truth_snapshot.get("id", "unknown")
        
        # Log the excluded trajectory
        log_excluded_trajectory(
            trajectory_id=trajectory_id,
            exclusion_reason=f"Ambiguous failure cause: {reason_code}",
            ambiguity_reason=reason_code,
            ground_truth_snapshot_id=ground_truth_snapshot.get("id", "unknown"),
            action_log_preview=action_log[:3] if action_log else []  # Log first 3 steps for context
        )
        
        return result
    
    result["exclusion_status"] = "INCLUDED"
    return result

def run_validation_with_ambiguity_handling(
    input_path: str,
    output_path: str,
    excluded_path: Optional[str] = None
) -> Dict[str, int]:
    """
    Run validation on a dataset of trajectories, handling ambiguous cases.
    
    Args:
        input_path: Path to input trajectories JSONL
        output_path: Path to save validated trajectories
        excluded_path: Path to save excluded trajectories (if None, uses default)
    
    Returns:
        Dict with counts of PASS, FAIL, AMBIGUOUS, EXCLUDED
    """
    # Set exclusion path if not provided
    if excluded_path is None:
        excluded_path = os.path.join(DATA_PATH, "raw", "excluded_log.json")
    
    set_exclusion_path(excluded_path)
    
    # Load ground truth
    ground_truth_map = {}
    gt_data = load_ground_truth_raw()
    for gt in gt_data:
        gt_id = gt.get("id")
        if gt_id:
            ground_truth_map[gt_id] = gt
    
    # Process trajectories
    validated_results = []
    counts = {"PASS": 0, "FAIL": 0, "AMBIGUOUS": 0, "EXCLUDED": 0}
    
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                trajectory = json.loads(line)
                trajectory_id = trajectory.get("trajectory_id", f"line_{line_num}")
                action_log = trajectory.get("action_log", [])
                
                # Find matching ground truth
                gt_snapshot = None
                for gt_id in trajectory.get("ground_truth_ids", []):
                    if gt_id in ground_truth_map:
                        gt_snapshot = ground_truth_map[gt_id]
                        break
                
                if gt_snapshot is None:
                    # No ground truth found, mark as ambiguous
                    result = process_trajectory_for_ambiguity(
                        trajectory_id, action_log, {"id": "missing_ground_truth"}
                    )
                else:
                    result = process_trajectory_for_ambiguity(
                        trajectory_id, action_log, gt_snapshot
                    )
                
                validated_results.append(result)
                counts[result["validation_status"]] += 1
                
            except json.JSONDecodeError as e:
                # Log malformed line as excluded
                excluded_result = {
                    "trajectory_id": f"malformed_line_{line_num}",
                    "validation_status": "EXCLUDED",
                    "reason_code": "json_parse_error",
                    "exclusion_status": "EXCLUDED",
                    "ambiguity_reason": "invalid_json_format",
                    "timestamp": datetime.utcnow().isoformat()
                }
                log_excluded_trajectory(
                    trajectory_id=f"malformed_line_{line_num}",
                    exclusion_reason="Invalid JSON format",
                    ambiguity_reason="invalid_json_format",
                    ground_truth_snapshot_id="unknown"
                )
                validated_results.append(excluded_result)
                counts["EXCLUDED"] += 1
    
    # Write validated results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for result in validated_results:
            f.write(json.dumps(result) + '\n')
    
    return counts

def run():
    """Main entry point for validation with ambiguity handling."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate trajectories with ambiguity handling")
    parser.add_argument("--input", required=True, help="Input trajectories JSONL file")
    parser.add_argument("--output", required=True, help="Output validated trajectories file")
    parser.add_argument("--excluded", default=None, help="Output excluded trajectories file")
    
    args = parser.parse_args()
    
    counts = run_validation_with_ambiguity_handling(
        input_path=args.input,
        output_path=args.output,
        excluded_path=args.excluded
    )
    
    print(f"Validation complete: {counts}")
    return counts

if __name__ == "__main__":
    run()
