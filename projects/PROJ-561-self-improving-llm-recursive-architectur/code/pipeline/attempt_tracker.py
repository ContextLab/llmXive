"""
Attempt Tracker Module for T126: Rollback & Verification State Machine.

Implements the state machine to handle cycle failures, degradation events,
and rollback logic as per FR-012.
"""
import json
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from config import get_config, get_trajectory_path
from results.trajectory_schema import read_trajectory, write_trajectory, TrajectoryEntry

logger = logging.getLogger(__name__)

class RollbackEventError(Exception):
    """Raised when a rollback event is triggered due to oracle failure or degradation."""
    pass

class FixedPointReachedError(Exception):
    """Raised when the system detects a fixed point (no improvement for N cycles)."""
    pass

def _load_cycle_state(cycle_id: int) -> Dict[str, Any]:
    """Load the state file for a specific cycle if it exists."""
    config = get_config()
    state_path = os.path.join(config.state_dir, f"cycle_{cycle_id}.yaml")
    if os.path.exists(state_path):
        import yaml
        with open(state_path, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}

def _save_cycle_state(cycle_id: int, state: Dict[str, Any]) -> None:
    """Save the state file for a specific cycle."""
    config = get_config()
    state_path = os.path.join(config.state_dir, f"cycle_{cycle_id}.yaml")
    os.makedirs(config.state_dir, exist_ok=True)
    import yaml
    with open(state_path, 'w') as f:
        yaml.dump(state, f)

def check_rollback_conditions(
    current_metrics: Dict[str, float],
    baseline_metrics: Dict[str, float],
    oracle_passed: bool,
    degradation_threshold: float = 0.05
) -> bool:
    """
    Determine if a rollback event should be triggered.
    
    Conditions:
    1. External Oracle Check failed (oracle_passed is False).
    2. Performance degradation >= degradation_threshold (5%).
    
    Returns True if rollback is required.
    """
    if not oracle_passed:
        logger.warning("Rollback Event: External Oracle Check failed.")
        return True

    # Check for degradation across benchmarks
    # We consider the primary metric (e.g., GSM8K accuracy) for degradation check
    # If multiple benchmarks exist, we might check the weighted average or the worst performer.
    # For this implementation, we check GSM8K if available, else the first available metric.
    primary_metric_key = 'gsm8k_accuracy'
    if primary_metric_key not in current_metrics and baseline_metrics:
        # Fallback to first key in baseline if specific one missing
        primary_metric_key = next(iter(baseline_metrics.keys()))

    if primary_metric_key in current_metrics and primary_metric_key in baseline_metrics:
        baseline_val = baseline_metrics[primary_metric_key]
        current_val = current_metrics[primary_metric_key]
        
        if baseline_val > 0:
            relative_change = (current_val - baseline_val) / baseline_val
            if relative_change < -degradation_threshold:
                logger.warning(f"Rollback Event: Degradation detected ({relative_change:.2%}) < {-degradation_threshold:.0%} threshold.")
                return True
        elif current_val < baseline_val:
             # If baseline was 0 and current is negative (unlikely for accuracy) or just lower
             logger.warning("Rollback Event: Performance dropped from zero baseline.")
             return True

    return False

def log_rollback_event(cycle_id: int, reason: str, trajectory_path: Optional[str] = None) -> None:
    """
    Log a rollback event to the trajectory and state.
    
    Adheres to FR-012: Does not revert weights, but increments cycle counter
    and ensures a new modification is attempted.
    """
    if trajectory_path is None:
        trajectory_path = get_trajectory_path()
    
    # Read current trajectory
    trajectory_data = read_trajectory(trajectory_path)
    
    # Find the entry for the current cycle
    entry = None
    for e in trajectory_data.entries:
        if e.cycle_id == cycle_id:
            entry = e
            break
    
    if entry:
        # Update the entry with rollback status
        entry.status = "rollback"
        entry.rollback_reason = reason
        entry.rollback_timestamp = datetime.now().isoformat()
        
        # Ensure the modification was marked as "failed" or "rejected"
        if not hasattr(entry, 'modification_status'):
            entry.modification_status = "rejected"
        else:
            entry.modification_status = "rejected"
        
        write_trajectory(trajectory_data, trajectory_path)
    
    logger.info(f"Rollback Event logged for Cycle {cycle_id}: {reason}")

def check_fixed_point_convergence(
    trajectory_path: Optional[str] = None,
    stagnation_cycles: int = 3,
    p_value_threshold: float = 0.05
) -> bool:
    """
    Check if the system has reached a fixed point.
    
    Returns True if:
    - 3 consecutive cycles show no statistically significant improvement (p > 0.05).
    - Parameter count is increasing (indicating continued cost without gain).
    """
    if trajectory_path is None:
        trajectory_path = get_trajectory_path()
    
    trajectory_data = read_trajectory(trajectory_path)
    entries = sorted(trajectory_data.entries, key=lambda x: x.cycle_id)
    
    if len(entries) < stagnation_cycles:
        return False
    
    recent_entries = entries[-stagnation_cycles:]
    
    all_stagnant = True
    params_increasing = True
    
    # We need to check the last N-1 transitions (comparing to the one before)
    # Or simply check if the last N entries are all stagnant relative to baseline?
    # The requirement says "3 consecutive cycles yield no statistically significant improvement".
    # This usually means comparing Cycle N to Cycle N-1, and if p > 0.05, it's stagnant.
    
    for i in range(1, len(recent_entries)):
        current = recent_entries[i]
        previous = recent_entries[i-1]
        
        # Check p-value from statistical test (stored in trajectory if T007 ran)
        # Assuming 'statistical_significance_p' field exists with p-value
        p_val = getattr(current, 'statistical_significance_p', 1.0)
        
        if p_val <= p_value_threshold:
            all_stagnant = False
            break
        
        # Check parameter count trend
        current_params = getattr(current, 'param_count', 0)
        previous_params = getattr(previous, 'param_count', 0)
        
        if current_params <= previous_params:
            # If params didn't increase, we might not be in the "costly stagnation" scenario
            # but strictly speaking, "Fixed Point" is just no improvement.
            # However, Von Neumann's concern is "infinite regress" of cost.
            # We flag if params are increasing (costing more) for no gain.
            pass 
        
        # We need to ensure params are increasing to trigger the specific "Fixed Point" warning
        # as per the task description: "parameter count is increasing"
        if current_params <= previous_params:
             params_increasing = False

    # If we have 3 stagnant cycles AND params are increasing
    if all_stagnant and params_increasing and len(recent_entries) >= stagnation_cycles:
        # Verify the last entry also had params > the one before it
        last = recent_entries[-1]
        second_last = recent_entries[-2]
        if getattr(last, 'param_count', 0) > getattr(second_last, 'param_count', 0):
            return True
    
    return False

def handle_cycle_failure(
    cycle_id: int,
    current_metrics: Dict[str, float],
    baseline_metrics: Dict[str, float],
    oracle_passed: bool,
    trajectory_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main entry point for handling a cycle failure.
    
    1. Check rollback conditions.
    2. If rollback, log event and return instruction to proceed to next cycle.
    3. Check fixed point convergence.
    4. Return state update for the orchestrator.
    """
    if trajectory_path is None:
        trajectory_path = get_trajectory_path()
    
    should_rollback = check_rollback_conditions(
        current_metrics, 
        baseline_metrics, 
        oracle_passed
    )
    
    result = {
        "cycle_id": cycle_id,
        "action": "continue",
        "next_cycle_id": cycle_id + 1,
        "rollback_triggered": False,
        "fixed_point_reached": False
    }
    
    if should_rollback:
        reason = "Oracle Failure" if not oracle_passed else "Performance Degradation"
        log_rollback_event(cycle_id, reason, trajectory_path)
        result["rollback_triggered"] = True
        result["action"] = "rollback_next_cycle"
        result["rollback_reason"] = reason
        
        # Force a new modification in the next cycle (logic handled by orchestrator)
        # We just signal that the current attempt was rejected.
    
    # Check for fixed point convergence
    if check_fixed_point_convergence(trajectory_path):
        result["fixed_point_reached"] = True
        result["action"] = "terminate_fixed_point"
        logger.critical("Fixed Point Reached: No further improvement detected after 3 stagnant cycles with increasing parameters.")
    
    return result

def check_attempt_limit(cycle_id: int, max_cycles: int = 3) -> bool:
    """
    Check if the cycle count has exceeded the maximum allowed attempts.
    This is a simple guard to prevent infinite loops.
    """
    if cycle_id >= max_cycles:
        logger.warning(f"Attempt limit reached: {cycle_id} >= {max_cycles}")
        return True
    return False

def get_attempt_message(cycle_id: int, status: str) -> str:
    """Generate a status message for the attempt."""
    if status == "rollback":
        return f"Cycle {cycle_id} rolled back due to oracle failure or degradation."
    elif status == "fixed_point":
        return f"Cycle {cycle_id} terminated: Fixed point reached."
    elif status == "success":
        return f"Cycle {cycle_id} completed successfully."
    else:
        return f"Cycle {cycle_id} status: {status}"
