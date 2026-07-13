import json
import os
import random
from typing import Any, Dict, List, Optional, Tuple

from utils.constants import get_coverage_vector_dimensions, get_semantic_proxies
from utils.logging import get_task_logger, log_error

logger = get_task_logger(__name__)

def initialize_scheduler_config() -> Dict[str, Any]:
    """
    Initialize the scheduler configuration with default parameters.
    Returns a dictionary containing all necessary configuration for the scheduler.
    """
    config = {
        "phase_1_coverage_threshold": 0.05,  # 5%
        "phase_2_min_success_rate": 0.10,
        "phase_2_max_success_rate": 0.90,
        "phase_2_target_success_rate": 0.50,
        "max_expansion_steps": 5,
        "entropy_fallback_threshold": 0.01,
        "batch_size": 10,
        "random_seed": 42,
    }
    random.seed(config["random_seed"])
    return config

def calculate_coverage_vector_mean(coverage_history: List[List[float]]) -> float:
    """
    Calculate the mean coverage across all dimensions and all history entries.
    Returns a single float representing the average coverage percentage.
    """
    if not coverage_history:
        return 0.0
    
    total_coverage = 0.0
    count = 0
    
    for entry in coverage_history:
        for value in entry:
            total_coverage += value
            count += 1
    
    if count == 0:
        return 0.0
    
    return total_coverage / count

def select_phase_1_task(
    available_tasks: List[Dict[str, Any]], 
    coverage_vector: List[float],
    config: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Phase 1: Select tasks that target uncovered states (coverage < 5%).
    Prioritizes tasks that cover the most zero-valued dimensions in the current vector.
    """
    threshold = config["phase_1_coverage_threshold"]
    uncovered_indices = [i for i, val in enumerate(coverage_vector) if val < threshold]
    
    if not uncovered_indices:
        logger.info("Phase 1: No uncovered states found.")
        return None
    
    # Score tasks by how many uncovered states they cover
    best_task = None
    max_uncovered_covered = -1
    
    for task in available_tasks:
        task_coverage = task.get("state_coverage", [])
        if len(task_coverage) != len(coverage_vector):
            continue
        
        covered_count = sum(
            1 for i in uncovered_indices if task_coverage[i] > 0
        )
        
        if covered_count > max_uncovered_covered:
            max_uncovered_covered = covered_count
            best_task = task
    
    if best_task and max_uncovered_covered > 0:
        logger.info(f"Phase 1: Selected task covering {max_uncovered_covered} uncovered states.")
        return best_task
    
    return None

def select_phase_2_task(
    available_tasks: List[Dict[str, Any]],
    coverage_vector: List[float],
    config: Dict[str, Any],
    success_history: List[float]
) -> Optional[Dict[str, Any]]:
    """
    Phase 2: Select tasks targeting moderate success rates (10-90%).
    Uses dynamic range expansion if no tasks found in current range.
    """
    min_success = config["phase_2_min_success_rate"]
    max_success = config["phase_2_max_success_rate"]
    target = config["phase_2_target_success_rate"]
    max_expansion = config["max_expansion_steps"]
    
    # Calculate current average success rate
    current_success = sum(success_history) / len(success_history) if success_history else 0.5
    
    # Expand range dynamically if needed
    for expansion_step in range(max_expansion + 1):
        current_min = max(0.0, min_success - (expansion_step * 0.1))
        current_max = min(1.0, max_success + (expansion_step * 0.1))
        
        candidates = []
        for task in available_tasks:
            task_difficulty = task.get("difficulty_estimate", 0.5)
            if current_min <= task_difficulty <= current_max:
                candidates.append(task)
        
        if candidates:
            # Select task closest to target success rate
            best_task = min(
                candidates,
                key=lambda t: abs(t.get("difficulty_estimate", 0.5) - target)
            )
            logger.info(f"Phase 2: Selected task with difficulty {best_task.get('difficulty_estimate'):.2f} "
                        f"(expanded range: {current_min:.2f}-{current_max:.2f})")
            return best_task
    
    logger.warning("Phase 2: No suitable tasks found after range expansion.")
    return None

def select_max_entropy_task(
    available_tasks: List[Dict[str, Any]],
    coverage_vector: List[float]
) -> Optional[Dict[str, Any]]:
    """
    Fallback: Select task that maximizes entropy (uncertainty) in state coverage.
    This ensures exploration when no specific coverage or difficulty targets are met.
    """
    best_task = None
    max_entropy = -1.0
    
    for task in available_tasks:
        task_coverage = task.get("state_coverage", [])
        if len(task_coverage) != len(coverage_vector):
            continue
        
        # Calculate entropy of the task's coverage vector
        entropy = 0.0
        for val in task_coverage:
            if val > 0 and val < 1:
                entropy -= val * (val + 1e-6)  # Avoid log(0)
        
        if entropy > max_entropy:
            max_entropy = entropy
            best_task = task
    
    if best_task:
        logger.info(f"Fallback: Selected max-entropy task (entropy={max_entropy:.4f})")
        return best_task
    
    return None

def run_static_random_scheduler(
    available_tasks: List[Dict[str, Any]],
    config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Static Random baseline: Randomly sample tasks without any state guidance.
    Used for experimental control (FR-003).
    """
    batch_size = config["batch_size"]
    selected = []
    
    for _ in range(min(batch_size, len(available_tasks))):
        if not available_tasks:
            break
        task = random.choice(available_tasks)
        selected.append(task)
    
    logger.info(f"Static Random: Selected {len(selected)} random tasks.")
    return selected

def run_scheduler(
    available_tasks: List[Dict[str, Any]],
    coverage_history: List[List[float]],
    success_history: List[float],
    config: Optional[Dict[str, Any]] = None
) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Main scheduler logic implementing the state-guided curriculum.
    
    Returns:
        Tuple of (selected_task, selection_reason)
        
    Logic:
        1. Calculate current mean coverage.
        2. If mean coverage < 5% (Phase 1), try to select task for uncovered states.
        3. If mean coverage >= 5% (Phase 2), try to select task for moderate success.
        4. If no task found in Phase 2, attempt range expansion.
        5. If still no task, fallback to max entropy.
        6. DEADLOCK PREVENTION: If all states are covered (mean coverage == 1.0) 
           OR if no tasks can be selected after all fallbacks, select randomly.
    """
    if config is None:
        config = initialize_scheduler_config()
    
    if not available_tasks:
        logger.error("No tasks available for scheduling.")
        return None, "no_tasks_available"
    
    current_coverage = coverage_history[-1] if coverage_history else [0.0] * get_coverage_vector_dimensions()
    mean_coverage = calculate_coverage_vector_mean(coverage_history)
    
    # DEADLOCK PREVENTION CHECK
    # If all states are fully covered (mean_coverage == 1.0), we risk a deadlock
    # where no specific coverage target can be met. We must fall back to random selection.
    if mean_coverage >= 1.0:
        logger.warning("Deadlock detected: All states covered (mean_coverage=1.0). "
                     "Switching to random selection to ensure progress.")
        selected = random.choice(available_tasks)
        return selected, "deadlock_prevention_random"
    
    # Phase 1: Low Coverage Targeting
    if mean_coverage < config["phase_1_coverage_threshold"]:
        task = select_phase_1_task(available_tasks, current_coverage, config)
        if task:
            return task, "phase_1_low_coverage"
    
    # Phase 2: Moderate Success Targeting
    task = select_phase_2_task(available_tasks, current_coverage, config, success_history)
    if task:
        return task, "phase_2_moderate_success"
    
    # Fallback 1: Max Entropy
    task = select_max_entropy_task(available_tasks, current_coverage)
    if task:
        return task, "fallback_max_entropy"
    
    # DEADLOCK PREVENTION: Final Fallback
    # If we reach here, no heuristic could find a task. This might happen if:
    # - All tasks have difficulty outside expanded ranges
    # - Coverage vectors are malformed
    # - The set of available tasks is exhausted of relevant options
    # In any case, we MUST select randomly to prevent the scheduler from stalling.
    logger.warning("Scheduler exhausted all heuristics. Activating deadlock prevention: Random Selection.")
    selected = random.choice(available_tasks)
    return selected, "deadlock_prevention_random_final_fallback"

def main():
    """
    Entry point for the scheduler module.
    Demonstrates the scheduler logic with mock data.
    """
    config = initialize_scheduler_config()
    
    # Mock available tasks
    mock_tasks = [
        {"id": "task_1", "difficulty_estimate": 0.2, "state_coverage": [1, 0, 0, 0, 0]},
        {"id": "task_2", "difficulty_estimate": 0.5, "state_coverage": [0, 1, 0, 0, 0]},
        {"id": "task_3", "difficulty_estimate": 0.8, "state_coverage": [0, 0, 1, 0, 0]},
        {"id": "task_4", "difficulty_estimate": 0.9, "state_coverage": [0, 0, 0, 1, 0]},
        {"id": "task_5", "difficulty_estimate": 0.1, "state_coverage": [0, 0, 0, 0, 1]},
    ]
    
    # Mock history
    mock_coverage_history = [
        [0.0, 0.0, 0.0, 0.0, 0.0],
        [0.2, 0.0, 0.0, 0.0, 0.0],
    ]
    mock_success_history = [0.3, 0.4, 0.35]
    
    # Test Phase 1
    task, reason = run_scheduler(mock_tasks, mock_coverage_history, mock_success_history, config)
    print(f"Selected Task: {task['id'] if task else None}, Reason: {reason}")
    
    # Test Deadlock Prevention (All states covered)
    full_coverage_history = [
        [1.0, 1.0, 1.0, 1.0, 1.0]
    ]
    task, reason = run_scheduler(mock_tasks, full_coverage_history, [0.5], config)
    print(f"Deadlock Test - Selected Task: {task['id'] if task else None}, Reason: {reason}")

if __name__ == "__main__":
    main()