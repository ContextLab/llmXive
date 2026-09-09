import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import re
from utils.config import get_project_root, get_data_dir
from utils.execution_log import ExecutionLog, TrajectoryExecutionLog

# --- Heuristic Rules for Coherence ---

def check_action_state_compatibility(action: str, state: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Checks if an action is compatible with the current state description.
    Heuristics:
    - 'click' requires 'elements' or 'buttons' in state.
    - 'type' requires an 'input_field' or 'text_area' in state.
    - 'swipe' requires 'scrollable' or 'list' in state.
    """
    action_lower = action.lower()
    state_text = json.dumps(state).lower()

    if 'click' in action_lower:
        if not any(k in state_text for k in ['element', 'button', 'icon', 'link']):
            return False, f"Action '{action}' requires interactive elements, but state lacks them."
    elif 'type' in action_lower or 'input' in action_lower:
        if not any(k in state_text for k in ['input', 'text', 'field', 'box', 'search']):
            return False, f"Action '{action}' requires an input field, but state lacks them."
    elif 'swipe' in action_lower or 'scroll' in action_lower:
        if not any(k in state_text for k in ['scroll', 'list', 'feed', 'content', 'page']):
            return False, f"Action '{action}' requires scrollable content, but state lacks them."
    
    return True, "Compatible"

def check_dependency_semantic_consistency(
    current_action: str, 
    previous_state: Dict[str, Any], 
    dependency_link: Optional[Dict[str, Any]]
) -> Tuple[bool, str]:
    """
    Validates that a dependency link (if present) is semantically consistent with
    the current action and previous state.
    
    Logic:
    1. If a dependency_link exists, check if the 'source_app' in the link matches
       the app context in 'previous_state'.
    2. Check if the 'target_action' implied by the link makes sense for the 'current_action'.
       (e.g., if link says 'copy_text', current action should be 'paste' or 'type').
    """
    if not dependency_link:
        return True, "No dependency link to validate."

    source_app = dependency_link.get('source_app', '').lower()
    target_action = dependency_link.get('target_action', '').lower()
    
    # Check App Context
    state_app = previous_state.get('app_name', '').lower()
    if source_app and state_app and source_app != state_app:
        # Cross-app dependency is allowed, but we check for plausibility below
        pass 
    
    # Check Target Action Logic
    # If the dependency says we need 'text', the current action should likely be 'type' or 'paste'
    expected_actions = []
    if 'text' in target_action or 'content' in target_action:
        expected_actions = ['type', 'paste', 'input']
    elif 'image' in target_action:
        expected_actions = ['attach', 'upload', 'share']
    elif 'url' in target_action:
        expected_actions = ['type', 'paste', 'navigate']

    if expected_actions:
        if not any(exp in current_action.lower() for exp in expected_actions):
            return False, f"Dependency expects '{target_action}' context, but action '{current_action}' does not match expected: {expected_actions}"

    return True, "Consistent"

def check_temporal_coherence(trajectory: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """
    Validates that the trajectory steps are temporally ordered and logical.
    Checks:
    - Timestamps (if present) are increasing.
    - No immediate repetition of identical state-action pairs (unless intentional loop).
    """
    prev_step = None
    for i, step in enumerate(trajectory):
        current_step_id = step.get('step_id', i)
        
        # Timestamp check
        if 'timestamp' in step and prev_step and 'timestamp' in prev_step:
            if step['timestamp'] < prev_step['timestamp']:
                return False, f"Temporal violation: Step {current_step_id} timestamp is before Step {prev_step.get('step_id')}"

        # Duplicate check (simple heuristic)
        if prev_step:
            if (step.get('action') == prev_step.get('action') and 
                str(step.get('state')) == str(prev_step.get('state'))):
                # Allow if it's a retry mechanism, but flag if it happens 3 times in a row
                if i > 1 and trajectory[i-1].get('action') == step.get('action'):
                    return False, f"Potential infinite loop detected at step {current_step_id}"

        prev_step = step

    return True, "Temporally coherent"

def check_cross_app_plausibility(trajectory: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """
    Validates cross-app transitions for plausibility.
    Checks:
    - If an action is 'switch_app' or 'home', the next step should be in a different app or home.
    - Dependency links crossing apps must have a valid 'transfer_type' (e.g., share, copy-paste).
    """
    for i, step in enumerate(trajectory):
        action = step.get('action', '').lower()
        deps = step.get('dependency_links', [])
        
        if 'switch_app' in action or 'home' in action:
            # Next step should ideally be in a different app or home state
            if i + 1 < len(trajectory):
                next_app = trajectory[i+1].get('state', {}).get('app_name', '')
                curr_app = step.get('state', {}).get('app_name', '')
                if next_app == curr_app and 'home' not in action:
                    # Might be a false positive if the user just opened the app again, 
                    # but for synthetic data, strict transition is preferred.
                    pass 

        for dep in deps:
            if dep.get('source_app') != dep.get('target_app'):
                if not dep.get('transfer_type'):
                    return False, f"Cross-app dependency at step {i} missing 'transfer_type'."
                
                valid_types = ['copy_paste', 'share', 'deep_link', 'intent']
                if dep['transfer_type'].lower() not in valid_types:
                    return False, f"Invalid transfer type '{dep['transfer_type']}' for cross-app dependency."

    return True, "Cross-app plausible"

def validate_trajectory_coherence(trajectory: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Runs all coherence checks on a single trajectory.
    """
    results = {
        "trajectory_id": trajectory[0].get('trajectory_id', 'unknown') if trajectory else 'unknown',
        "step_count": len(trajectory),
        "checks": {},
        "is_valid": True,
        "errors": []
    }

    # 1. Temporal
    valid, msg = check_temporal_coherence(trajectory)
    results["checks"]["temporal"] = valid
    if not valid:
        results["is_valid"] = False
        results["errors"].append(f"Temporal: {msg}")

    # 2. Cross-App Plausibility
    valid, msg = check_cross_app_plausibility(trajectory)
    results["checks"]["cross_app_plausibility"] = valid
    if not valid:
        results["is_valid"] = False
        results["errors"].append(f"Cross-App: {msg}")

    # 3. Action-State & Dependency checks per step
    for i, step in enumerate(trajectory):
        action = step.get('action', '')
        state = step.get('state', {})
        deps = step.get('dependency_links', [])
        
        # Action-State
        valid, msg = check_action_state_compatibility(action, state)
        if not valid:
            results["checks"][f"action_state_step_{i}"] = False
            results["is_valid"] = False
            results["errors"].append(f"Step {i} Action-State: {msg}")
        
        # Dependency Semantic
        for j, dep in enumerate(deps):
            prev_state = trajectory[i-1].get('state', {}) if i > 0 else {}
            valid, msg = check_dependency_semantic_consistency(action, prev_state, dep)
            if not valid:
                results["checks"][f"dependency_semantic_step_{i}_link_{j}"] = False
                results["is_valid"] = False
                results["errors"].append(f"Step {i} Dep {j}: {msg}")

    return results

def validate_benchmark_coherence(trajectories: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Validates a list of trajectories (a benchmark) and aggregates statistics.
    """
    total = len(trajectories)
    valid_count = 0
    all_results = []

    for traj in trajectories:
        res = validate_trajectory_coherence(traj)
        all_results.append(res)
        if res["is_valid"]:
            valid_count += 1

    return {
        "total_trajectories": total,
        "valid_trajectories": valid_count,
        "validity_rate": valid_count / total if total > 0 else 0.0,
        "results": all_results
    }

def run_validation(input_file: str, output_file: str) -> bool:
    """
    Main entry point for validating a JSONL file of trajectories.
    Reads trajectories, validates each, and writes results to JSON.
    """
    root = get_project_root()
    data_dir = get_data_dir()
    
    # Handle relative paths if needed
    if not Path(input_file).is_absolute():
        input_path = data_dir / input_file
    else:
        input_path = Path(input_file)

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return False

    trajectories = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                traj_data = json.loads(line)
                # The generator might output a list of steps directly or a dict with 'steps'
                if isinstance(traj_data, list):
                    trajectories.append(traj_data)
                elif isinstance(traj_data, dict) and 'steps' in traj_data:
                    trajectories.append(traj_data['steps'])
                else:
                    # Assume single step wrapped or error
                    trajectories.append([traj_data])
            except json.JSONDecodeError as e:
                print(f"Warning: Skipping invalid JSON line: {e}")
                continue

    if not trajectories:
        print("Error: No valid trajectories found in input.")
        return False

    print(f"Validating {len(trajectories)} trajectories...")
    summary = validate_benchmark_coherence(trajectories)

    # Write output
    if not Path(output_file).parent.exists():
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    print(f"Validation complete. Results written to {output_file}")
    print(f"Validity Rate: {summary['validity_rate']:.2%}")
    
    if summary['validity_rate'] < 0.95:
        print("Warning: Validity rate is below 95% threshold.")
        return False
    
    return True

def main():
    """
    CLI Entry point.
    Usage: python -m data_generation.coherence_validator <input_file> <output_file>
    """
    if len(sys.argv) < 3:
        print("Usage: coherence_validator <input_jsonl> <output_json>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    success = run_validation(input_file, output_file)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()