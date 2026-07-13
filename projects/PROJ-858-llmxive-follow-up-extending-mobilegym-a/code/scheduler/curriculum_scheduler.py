import json
import math
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import from project API surface
from utils.constants import calculate_coverage_ratio, is_valid_coverage_vector
from utils.logging import get_logger, log_with_context, SchedulerError

logger = get_logger(__name__)

class CurriculumScheduler:
    """
    Dynamic Curriculum Scheduler for MobileGym.
    Implements state-guided task selection based on coverage vectors.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.low_coverage_threshold = self.config.get("low_coverage_threshold", 0.05)
        self.sweet_spot_min = self.config.get("sweet_spot_min", 0.30)
        self.sweet_spot_max = self.config.get("sweet_spot_max", 0.70)
        self.entropy_weight = self.config.get("entropy_weight", 1.0)
        self.batch_size = self.config.get("batch_size", 10)
        
        # Deadlock prevention settings
        self.deadlock_threshold = self.config.get("deadlock_threshold", 0.99)
        self.random_selection_probability = self.config.get("random_selection_probability", 0.1)

    def _calculate_entropy(self, coverage_vector: List[int]) -> float:
        """Calculate entropy of the coverage vector."""
        if not coverage_vector:
            return 0.0
        
        total_bits = len(coverage_vector)
        ones_count = sum(coverage_vector)
        zeros_count = total_bits - ones_count
        
        if ones_count == 0 or zeros_count == 0:
            return 0.0
        
        p_ones = ones_count / total_bits
        p_zeros = zeros_count / total_bits
        
        entropy = - (p_ones * math.log2(p_ones) + p_zeros * math.log2(p_zeros))
        return entropy

    def _calculate_task_difficulty(self, task_params: Dict[str, Any]) -> float:
        """
        Estimate task difficulty based on parameters.
        This is a placeholder - in real implementation, this would use
        historical success rates or complexity metrics.
        """
        # Simple heuristic: more complex parameters = higher difficulty
        complexity_score = 0.0
        
        if "num_steps" in task_params:
            complexity_score += min(task_params["num_steps"] / 100.0, 1.0)
        if "num_objects" in task_params:
            complexity_score += min(task_params["num_objects"] / 20.0, 1.0)
        if "state_variables" in task_params:
            complexity_score += min(len(task_params["state_variables"]) / 10.0, 1.0)
        
        return min(complexity_score, 1.0)

    def _select_low_coverage_tasks(
        self, 
        available_tasks: List[Dict[str, Any]], 
        current_coverage: List[int]
    ) -> List[Dict[str, Any]]:
        """Select tasks that target low coverage states."""
        if not available_tasks:
            return []
        
        selected = []
        current_ratio = calculate_coverage_ratio(current_coverage)
        
        if current_ratio >= self.low_coverage_threshold:
            # We're above the low coverage threshold, don't prioritize this phase
            return []
        
        # Score tasks by how much they would improve coverage
        for task in available_tasks:
            task_state_vars = task.get("state_variables", [])
            if not task_state_vars:
                continue
            
            # Calculate potential coverage gain
            potential_gain = 0
            for var in task_state_vars:
                # Assuming task state variables map to indices in coverage vector
                # In real implementation, this would use a mapping from variable names to indices
                var_index = hash(var) % len(current_coverage) if current_coverage else 0
                if current_coverage[var_index] == 0:
                    potential_gain += 1
            
            task["potential_coverage_gain"] = potential_gain
            selected.append(task)
        
        # Sort by potential gain (descending)
        selected.sort(key=lambda x: x.get("potential_coverage_gain", 0), reverse=True)
        
        return selected[:self.batch_size]

    def _select_sweet_spot_tasks(
        self, 
        available_tasks: List[Dict[str, Any]], 
        current_coverage: List[int]
    ) -> List[Dict[str, Any]]:
        """Select tasks in the moderate success rate range (sweet spot)."""
        if not available_tasks:
            return []
        
        selected = []
        current_ratio = calculate_coverage_ratio(current_coverage)
        
        # Filter tasks that are likely to achieve moderate success
        for task in available_tasks:
            difficulty = self._calculate_task_difficulty(task)
            
            # Sweet spot: tasks with difficulty that should yield 30-70% success
            # This is a simplified heuristic
            if self.sweet_spot_min <= difficulty <= self.sweet_spot_max:
                selected.append(task)
        
        # If we have tasks in the sweet spot, return them
        if selected:
            # Sort by difficulty to get a range
            selected.sort(key=lambda x: self._calculate_task_difficulty(x))
            return selected[:self.batch_size]
        
        # If no tasks in sweet spot, try to expand range
        expanded_tasks = []
        for task in available_tasks:
            difficulty = self._calculate_task_difficulty(task)
            # Expand to 10-90% range
            if 0.10 <= difficulty <= 0.90:
                expanded_tasks.append(task)
        
        if expanded_tasks:
            expanded_tasks.sort(key=lambda x: self._calculate_task_difficulty(x))
            return expanded_tasks[:self.batch_size]
        
        return []

    def _select_by_max_entropy(
        self, 
        available_tasks: List[Dict[str, Any]], 
        current_coverage: List[int]
    ) -> List[Dict[str, Any]]:
        """Select tasks that maximize entropy of the coverage vector."""
        if not available_tasks:
            return []
        
        # Calculate current entropy
        current_entropy = self._calculate_entropy(current_coverage)
        
        # Score tasks by potential entropy increase
        scored_tasks = []
        for task in available_tasks:
            task_state_vars = task.get("state_variables", [])
            if not task_state_vars:
                continue
            
            # Simulate adding this task's coverage
            simulated_coverage = current_coverage.copy()
            for var in task_state_vars:
                var_index = hash(var) % len(simulated_coverage) if simulated_coverage else 0
                simulated_coverage[var_index] = 1
            
            new_entropy = self._calculate_entropy(simulated_coverage)
            entropy_gain = new_entropy - current_entropy
            
            task["entropy_gain"] = entropy_gain
            scored_tasks.append(task)
        
        # Sort by entropy gain (descending)
        scored_tasks.sort(key=lambda x: x.get("entropy_gain", 0), reverse=True)
        
        return scored_tasks[:self.batch_size]

    def _select_random_tasks(
        self, 
        available_tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Randomly select tasks (baseline)."""
        if not available_tasks:
            return []
        
        selected = random.sample(available_tasks, min(len(available_tasks), self.batch_size))
        return selected

    def _check_deadlock_condition(self, current_coverage: List[int]) -> bool:
        """
        Check if we're in a deadlock condition (all or nearly all states covered).
        Returns True if random selection should be used to prevent stagnation.
        """
        if not current_coverage:
            return False
        
        coverage_ratio = calculate_coverage_ratio(current_coverage)
        return coverage_ratio >= self.deadlock_threshold

    def select_batch(
        self, 
        available_tasks: List[Dict[str, Any]], 
        current_coverage: List[int],
        history: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Select a batch of tasks based on the curriculum strategy.
        
        Args:
            available_tasks: List of available task configurations
            current_coverage: Current state coverage vector
            history: Optional history of previous selections and outcomes
        
        Returns:
            Tuple of (selected_tasks, selection_metadata)
        """
        if not available_tasks:
            raise SchedulerError("No available tasks for selection")
        
        if not is_valid_coverage_vector(current_coverage):
            raise SchedulerError(f"Invalid coverage vector: {current_coverage}")
        
        selection_metadata = {
            "timestamp": datetime.now().isoformat(),
            "current_coverage_ratio": calculate_coverage_ratio(current_coverage),
            "selection_method": None,
            "metrics_triggered": []
        }
        
        # Check for deadlock condition first
        if self._check_deadlock_condition(current_coverage):
            logger.info("Deadlock condition detected: all states covered. Using random selection.")
            selected = self._select_random_tasks(available_tasks)
            selection_metadata["selection_method"] = "random_deadlock_prevention"
            selection_metadata["metrics_triggered"].append({
                "metric": "deadlock_threshold",
                "value": calculate_coverage_ratio(current_coverage),
                "threshold": self.deadlock_threshold,
                "action": "random_selection"
            })
            return selected, selection_metadata
        
        # Phase 1: Low coverage targeting
        low_coverage_tasks = self._select_low_coverage_tasks(available_tasks, current_coverage)
        if low_coverage_tasks:
            selected = low_coverage_tasks
            selection_metadata["selection_method"] = "low_coverage_phase"
            selection_metadata["metrics_triggered"].append({
                "metric": "coverage_ratio",
                "value": calculate_coverage_ratio(current_coverage),
                "threshold": self.low_coverage_threshold,
                "action": "low_coverage_targeting"
            })
            return selected, selection_metadata
        
        # Phase 2: Sweet spot targeting
        sweet_spot_tasks = self._select_sweet_spot_tasks(available_tasks, current_coverage)
        if sweet_spot_tasks:
            selected = sweet_spot_tasks
            selection_metadata["selection_method"] = "sweet_spot_phase"
            selection_metadata["metrics_triggered"].append({
                "metric": "task_difficulty",
                "range": [self.sweet_spot_min, self.sweet_spot_max],
                "action": "sweet_spot_targeting"
            })
            return selected, selection_metadata
        
        # Fallback: Max entropy selection
        entropy_tasks = self._select_by_max_entropy(available_tasks, current_coverage)
        if entropy_tasks:
            selected = entropy_tasks
            selection_metadata["selection_method"] = "max_entropy_fallback"
            selection_metadata["metrics_triggered"].append({
                "metric": "fallback",
                "reason": "no_sweet_spot_tasks",
                "action": "max_entropy_selection"
            })
            return selected, selection_metadata
        
        # Ultimate fallback: Random selection
        selected = self._select_random_tasks(available_tasks)
        selection_metadata["selection_method"] = "random_ultimate_fallback"
        selection_metadata["metrics_triggered"].append({
            "metric": "fallback",
            "reason": "all_strategies_exhausted",
            "action": "random_selection"
        })
        
        return selected, selection_metadata

    def get_static_random_batch(
        self, 
        available_tasks: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Generate a batch using static random sampling (baseline).
        
        Args:
            available_tasks: List of available task configurations
        
        Returns:
            Tuple of (selected_tasks, selection_metadata)
        """
        selected = self._select_random_tasks(available_tasks)
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "selection_method": "static_random_baseline",
            "metrics_triggered": []
        }
        return selected, metadata


def main():
    """
    Main entry point for testing the scheduler.
    This demonstrates the deadlock prevention mechanism.
    """
    # Sample configuration
    config = {
        "low_coverage_threshold": 0.05,
        "sweet_spot_min": 0.30,
        "sweet_spot_max": 0.70,
        "deadlock_threshold": 0.99,
        "batch_size": 5
    }
    
    scheduler = CurriculumScheduler(config)
    
    # Create sample tasks
    sample_tasks = [
        {
            "task_id": f"task_{i}",
            "state_variables": [f"var_{j}" for j in range(i % 5 + 1)],
            "num_steps": 50 + i * 10,
            "num_objects": 5 + i
        }
        for i in range(20)
    ]
    
    # Test 1: Normal operation with low coverage
    print("Test 1: Low coverage scenario")
    low_coverage = [0] * 10  # 0% coverage
    selected, meta = scheduler.select_batch(sample_tasks, low_coverage)
    print(f"  Selected {len(selected)} tasks using method: {meta['selection_method']}")
    print(f"  Metrics triggered: {meta['metrics_triggered']}")
    
    # Test 2: Sweet spot scenario
    print("\nTest 2: Sweet spot scenario")
    medium_coverage = [1] * 5 + [0] * 5  # 50% coverage
    selected, meta = scheduler.select_batch(sample_tasks, medium_coverage)
    print(f"  Selected {len(selected)} tasks using method: {meta['selection_method']}")
    print(f"  Metrics triggered: {meta['metrics_triggered']}")
    
    # Test 3: Deadlock prevention (all states covered)
    print("\nTest 3: Deadlock prevention scenario")
    full_coverage = [1] * 10  # 100% coverage
    selected, meta = scheduler.select_batch(sample_tasks, full_coverage)
    print(f"  Selected {len(selected)} tasks using method: {meta['selection_method']}")
    print(f"  Metrics triggered: {meta['metrics_triggered']}")
    
    # Test 4: Static random baseline
    print("\nTest 4: Static random baseline")
    selected, meta = scheduler.get_static_random_batch(sample_tasks)
    print(f"  Selected {len(selected)} tasks using method: {meta['selection_method']}")
    
    print("\nAll tests completed successfully!")


if __name__ == "__main__":
    main()