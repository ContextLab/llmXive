import json
import os
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from src.config.config import DATA_PATH, SEED

# Import exclusion logger to handle ambiguous cases
from src.sim.exclusion_logger import log_excluded_trajectory, set_exclusion_path

# Import ground truth loading from T007a
# Assuming T007a populated this function or we load directly
# Since T007a is marked completed, we assume the file exists and is readable
# We will implement the loading logic here to be safe and self-contained

def load_ground_truth_raw(filepath: str) -> List[Dict[str, Any]]:
    """
    Load ground truth raw data from JSON file.
    T007a ensures this file exists at data/raw/ground_truth_raw.json
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Ground truth raw file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        return json.load(f)

def validate_trajectory(trajectory: Dict[str, Any], ground_truth: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate a trajectory against ground truth.
    
    Returns:
        (is_valid, reason_code, ground_truth_snapshot_id)
        - is_valid: True if trajectory matches ground truth
        - reason_code: Code indicating validation status (PASS, FAIL, AMBIGUOUS)
        - ground_truth_snapshot_id: ID of the ground truth entry used
    """
    # Check if trajectory has required fields
    if 'action_log' not in trajectory or 'trajectory_id' not in trajectory:
        return False, "MISSING_FIELDS", None
    
    # Check if ground truth has required fields
    if 'transitions' not in ground_truth or 'snapshot_id' not in ground_truth:
        return False, "INVALID_GROUND_TRUTH", None
    
    # Extract action log and ground truth transitions
    action_log = trajectory.get('action_log', [])
    transitions = ground_truth.get('transitions', [])
    
    # Deterministic priority rule: Check transitions in order
    # If multiple causes are found that cannot be resolved by priority, mark as AMBIGUOUS
    causes = []
    
    for i, action in enumerate(action_log):
        # Check if this action matches a ground truth transition
        matched = False
        for j, transition in enumerate(transitions):
            expected_action = transition.get('expected_action')
            expected_state = transition.get('expected_state')
            actual_state = action.get('state')
            
            # Simple matching logic - in real implementation, this would be more complex
            if expected_action and expected_action == action.get('action'):
                if expected_state and expected_state == actual_state:
                    matched = True
                    break
        
        if not matched:
            causes.append({
                'step': i,
                'action': action.get('action'),
                'expected': transitions[i] if i < len(transitions) else None
            })
    
    # Apply deterministic priority rule
    if len(causes) == 0:
        return True, "PASS", ground_truth.get('snapshot_id')
    elif len(causes) == 1:
        # Single cause found - not ambiguous
        return False, "FAIL", ground_truth.get('snapshot_id')
    else:
        # Multiple causes found - check if they can be resolved by priority rule
        # Priority rule: First mismatch is the primary cause
        # If multiple mismatches are equally valid (e.g., same step, different interpretations), it's ambiguous
        
        # For now, if we have multiple distinct causes at different steps, we use the first one (priority rule)
        # If we have multiple causes at the same step with different interpretations, it's ambiguous
        
        ambiguous = False
        for i, cause1 in enumerate(causes):
            for j, cause2 in enumerate(causes):
                if i < j and cause1['step'] == cause2['step']:
                    # Same step, different interpretations - ambiguous
                    ambiguous = True
                    break
            if ambiguous:
                break
        
        if ambiguous:
            return False, "AMBIGUOUS", ground_truth.get('snapshot_id')
        else:
            # Use first cause as per priority rule
            return False, "FAIL", ground_truth.get('snapshot_id')

def process_trajectory_for_ambiguity(trajectory: Dict[str, Any], ground_truth: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a trajectory to determine if it's ambiguous.
    
    Returns:
        Dict with validation status and ambiguity details
    """
    is_valid, reason_code, gt_id = validate_trajectory(trajectory, ground_truth)
    
    result = {
        'trajectory_id': trajectory.get('trajectory_id'),
        'validation_status': reason_code,
        'ground_truth_snapshot_id': gt_id,
        'is_ambiguous': reason_code == "AMBIGUOUS"
    }
    
    if reason_code == "AMBIGUOUS":
        # Generate ambiguity reason
        action_log = trajectory.get('action_log', [])
        transitions = ground_truth.get('transitions', [])
        
        causes = []
        for i, action in enumerate(action_log):
            matched = False
            for j, transition in enumerate(transitions):
                expected_action = transition.get('expected_action')
                if expected_action and expected_action == action.get('action'):
                    matched = True
                    break
            
            if not matched:
                causes.append({
                    'step': i,
                    'action': action.get('action')
                })
        
        # Find ambiguous steps (multiple causes at same step)
        ambiguous_steps = []
        for i, cause1 in enumerate(causes):
            for j, cause2 in enumerate(causes):
                if i < j and cause1['step'] == cause2['step']:
                    ambiguous_steps.append(cause1['step'])
                    break
        
        result['ambiguity_reason'] = f"Multiple failure causes detected at steps: {ambiguous_steps}. Cannot resolve with deterministic priority rule."
    
    return result

def run_validation_with_ambiguity_handling(input_file: str, output_file: str, excluded_file: str) -> Dict[str, Any]:
    """
    Run validation on all trajectories and handle ambiguous cases.
    
    Ambiguous trajectories are logged to excluded_file with ambiguity_reason.
    Valid and non-ambiguous failures are saved to output_file.
    """
    # Load ground truth
    gt_path = os.path.join(DATA_PATH, 'raw', 'ground_truth_raw.json')
    ground_truth_data = load_ground_truth_raw(gt_path)
    
    # Create a map of ground truth by ID for quick lookup
    gt_map = {}
    for gt in ground_truth_data:
        gt_id = gt.get('snapshot_id')
        if gt_id:
            gt_map[gt_id] = gt
    
    # Load input trajectories
    with open(input_file, 'r') as f:
        trajectories = json.load(f)
    
    validated_trajectories = []
    excluded_trajectories = []
    
    for traj in trajectories:
        traj_id = traj.get('trajectory_id')
        
        # Try to find matching ground truth
        gt_id = traj.get('ground_truth_id')
        if gt_id and gt_id in gt_map:
            gt = gt_map[gt_id]
            result = process_trajectory_for_ambiguity(traj, gt)
            
            if result['validation_status'] == "AMBIGUOUS":
                # Log to excluded file
                excluded_entry = {
                    'trajectory_id': traj_id,
                    'ambiguity_reason': result.get('ambiguity_reason', 'Unknown ambiguity'),
                    'timestamp': datetime.now().isoformat(),
                    'ground_truth_snapshot_id': result.get('ground_truth_snapshot_id')
                }
                excluded_trajectories.append(excluded_entry)
            else:
                # Add validation result to trajectory
                traj['validation_status'] = result['validation_status']
                traj['ground_truth_snapshot_id'] = result.get('ground_truth_snapshot_id')
                validated_trajectories.append(traj)
        else:
            # No ground truth found - mark as failed
            traj['validation_status'] = "FAIL"
            traj['ground_truth_snapshot_id'] = None
            validated_trajectories.append(traj)
    
    # Write excluded trajectories to file
    os.makedirs(os.path.dirname(excluded_file), exist_ok=True)
    with open(excluded_file, 'w') as f:
        json.dump(excluded_trajectories, f, indent=2)
    
    # Write validated trajectories to file
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(validated_trajectories, f, indent=2)
    
    return {
        'total_processed': len(trajectories),
        'validated': len(validated_trajectories),
        'excluded': len(excluded_trajectories),
        'excluded_file': excluded_file,
        'output_file': output_file
    }

def run():
    """
    Main entry point for validation with ambiguity handling.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate trajectories with ambiguity handling')
    parser.add_argument('--input', required=True, help='Input trajectories file')
    parser.add_argument('--output', required=True, help='Output validated trajectories file')
    parser.add_argument('--excluded', default=os.path.join(DATA_PATH, 'raw', 'excluded_log.json'),
                      help='Output excluded trajectories file')
    
    args = parser.parse_args()
    
    result = run_validation_with_ambiguity_handling(args.input, args.output, args.excluded)
    
    print(f"Validation complete:")
    print(f"  Total processed: {result['total_processed']}")
    print(f"  Validated: {result['validated']}")
    print(f"  Excluded: {result['excluded']}")
    print(f"  Excluded file: {result['excluded_file']}")
    print(f"  Output file: {result['output_file']}")

if __name__ == '__main__':
    run()
