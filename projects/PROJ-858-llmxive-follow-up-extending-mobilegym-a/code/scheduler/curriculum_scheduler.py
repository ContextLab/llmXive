import json
import math
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from utils.logging import get_logger, log_with_context, log_error
from utils.constants import calculate_coverage_ratio

logger = get_logger(__name__)

class CurriculumScheduler:
    """
    Dynamic curriculum scheduler that selects tasks based on state coverage
    and success rate targets. Implements a two-phase logic:
    
    Phase 1: Target low coverage (< 5%) to explore new state space.
    Phase 2: Target moderate success rate (dynamic range expansion 10-90%)
             to optimize learning in the "sweet spot".
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.phase = 1
        self.low_coverage_threshold = config.get("low_coverage_threshold", 0.05)
        self.sweet_spot_min = config.get("sweet_spot_min", 0.10)
        self.sweet_spot_max = config.get("sweet_spot_max", 0.90)
        self.current_min = self.sweet_spot_min
        self.current_max = self.sweet_spot_max
        self.expansion_rate = config.get("expansion_rate", 0.1)
        self.logger = get_logger(__name__)
        
        # Constants for Phase 1
        self.phase1_target_coverage = config.get("phase1_target_coverage", 0.05)
        
    def _calculate_task_difficulty(self, task: Dict[str, Any], history: List[Dict[str, Any]]) -> float:
        """
        Calculate difficulty score for a task based on historical success rates.
        Returns a value between 0.0 (easy) and 1.0 (hard).
        """
        task_id = task.get("id")
        
        # Find historical results for this task
        task_history = [h for h in history if h.get("task_id") == task_id]
        
        if not task_history:
            # No history - assume medium difficulty
            return 0.5
        
        # Calculate success rate from history
        success_count = sum(1 for h in task_history if h.get("success", False))
        total_count = len(task_history)
        success_rate = success_count / total_count if total_count > 0 else 0.5
        
        # Invert success rate to get difficulty (0.0 = easy, 1.0 = hard)
        return 1.0 - success_rate
    
    def _select_low_coverage_tasks(
        self, 
        tasks: List[Dict[str, Any]], 
        current_coverage: List[float]
    ) -> List[Dict[str, Any]]:
        """
        Phase 1: Select tasks that target uncovered state variables.
        Prioritizes tasks that cover state variables with low current coverage.
        """
        if not tasks:
            return []
        
        # Calculate coverage ratio for each task based on current state coverage
        task_scores = []
        
        for task in tasks:
            task_coverage_vector = task.get("coverage_vector", [])
            if not task_coverage_vector:
                continue
            
            # Calculate how much new coverage this task would provide
            new_coverage_score = 0.0
            for i, (task_bit, current_val) in enumerate(zip(task_coverage_vector, current_coverage)):
                if task_bit == 1 and current_val < self.low_coverage_threshold:
                    new_coverage_score += 1.0
            
            # Normalize score
            if task_coverage_vector:
                new_coverage_score /= len(task_coverage_vector)
            
            task_scores.append((task, new_coverage_score))
        
        # Sort by coverage score (descending)
        task_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top tasks that provide significant new coverage
        selected_tasks = []
        for task, score in task_scores:
            if score > 0.0:  # Only select tasks that cover uncovered variables
                selected_tasks.append(task)
        
        return selected_tasks
    
    def _select_moderate_success_tasks(
        self,
        tasks: List[Dict[str, Any]],
        history: List[Dict[str, Any]],
        min_success_rate: float,
        max_success_rate: float
    ) -> List[Dict[str, Any]]:
        """
        Phase 2: Select tasks with success rates in the target range.
        Implements dynamic range expansion from (10-90%) as training progresses.
        """
        if not tasks:
            return []
        
        # Calculate success rates for each task
        task_success_rates = []
        
        for task in tasks:
            task_id = task.get("id")
            
            # Find historical results for this task
            task_history = [h for h in history if h.get("task_id") == task_id]
            
            if not task_history:
                # No history - assume medium difficulty (0.5 success rate)
                success_rate = 0.5
            else:
                success_count = sum(1 for h in task_history if h.get("success", False))
                total_count = len(task_history)
                success_rate = success_count / total_count if total_count > 0 else 0.5
            
            task_success_rates.append((task, success_rate))
        
        # Filter tasks within the target success rate range
        selected_tasks = []
        for task, success_rate in task_success_rates:
            if min_success_rate <= success_rate <= max_success_rate:
                selected_tasks.append(task)
        
        # If no tasks in range, expand the range dynamically
        if not selected_tasks:
            self.logger.info(
                f"No tasks found in range [{min_success_rate:.2f}, {max_success_rate:.2f}]. "
                f"Expanding range..."
            )
            
            # Expand range by expansion_rate
            new_min = max(0.0, min_success_rate - self.expansion_rate)
            new_max = min(1.0, max_success_rate + self.expansion_rate)
            
            # Check if we've reached the full range (10-90%)
            if new_min <= 0.1 and new_max >= 0.9:
                self.logger.warning(
                    "Range expansion reached limits (10-90%). Falling back to maximum entropy selection."
                )
                # Fallback: return tasks with most variance in success rates
                task_success_rates.sort(key=lambda x: x[1])
                # Return tasks from both ends of the spectrum
                mid = len(task_success_rates) // 2
                selected_tasks = [t for t, _ in task_success_rates[:mid//2] + task_success_rates[-mid//2:]]
            else:
                # Retry with expanded range
                selected_tasks = [
                    task for task, success_rate in task_success_rates
                    if new_min <= success_rate <= new_max
                ]
                # Update current range for next iteration
                self.current_min = new_min
                self.current_max = new_max
        
        return selected_tasks
    
    def _update_phase(self, history: List[Dict[str, Any]]) -> None:
        """
        Update the current phase based on overall progress.
        Transition from Phase 1 to Phase 2 when sufficient coverage is achieved.
        """
        if not history:
            return
        
        # Calculate overall success rate
        total_success = sum(1 for h in history if h.get("success", False))
        total_count = len(history)
        overall_success_rate = total_success / total_count if total_count > 0 else 0.0
        
        # Transition to Phase 2 if success rate is above threshold
        phase_transition_threshold = self.config.get("phase_transition_threshold", 0.3)
        
        if self.phase == 1 and overall_success_rate >= phase_transition_threshold:
            self.phase = 2
            self.logger.info(
                f"Transitioned to Phase 2. Overall success rate: {overall_success_rate:.2f}"
            )
        
        # Within Phase 2, expand range if success rate is consistently high
        if self.phase == 2 and overall_success_rate > 0.8:
            # Expand range towards the 10-90% bounds
            if self.current_min > 0.1:
                self.current_min = max(0.1, self.current_min - self.expansion_rate)
            if self.current_max < 0.9:
                self.current_max = min(0.9, self.current_max + self.expansion_rate)
            
            self.logger.info(
                f"Phase 2 range expanded to [{self.current_min:.2f}, {self.current_max:.2f}]"
            )
    
    def select_tasks(
        self,
        tasks: List[Dict[str, Any]],
        history: List[Dict[str, Any]],
        current_coverage: List[float],
        batch_size: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Main entry point for task selection.
        
        Args:
            tasks: List of available tasks with metadata
            history: List of historical rollout results
            current_coverage: Current state coverage vector
            batch_size: Number of tasks to select
        
        Returns:
            List of selected tasks
        """
        # Update phase based on history
        self._update_phase(history)
        
        selected_tasks = []
        
        if self.phase == 1:
            # Phase 1: Focus on low coverage exploration
            self.logger.info("Phase 1: Selecting tasks for low coverage exploration")
            selected_tasks = self._select_low_coverage_tasks(tasks, current_coverage)
            
            if not selected_tasks:
                # Fallback to random selection if no low coverage tasks found
                self.logger.warning("No low coverage tasks found. Falling back to random selection.")
                selected_tasks = random.sample(tasks, min(batch_size, len(tasks)))
        
        elif self.phase == 2:
            # Phase 2: Focus on moderate success rate optimization
            self.logger.info(
                f"Phase 2: Selecting tasks with success rate in "
                f"[{self.current_min:.2f}, {self.current_max:.2f}]"
            )
            selected_tasks = self._select_moderate_success_tasks(
                tasks, history, self.current_min, self.current_max
            )
            
            if not selected_tasks:
                # Fallback to maximum entropy or random selection
                self.logger.warning(
                    "No tasks found in target range. Falling back to maximum entropy selection."
                )
                # Fallback: select tasks with most diverse difficulty levels
                task_difficulties = [
                    (task, self._calculate_task_difficulty(task, history))
                    for task in tasks
                ]
                task_difficulties.sort(key=lambda x: x[1])
                # Select tasks from different difficulty levels
                step = max(1, len(task_difficulties) // batch_size)
                selected_tasks = [
                    task for task, _ in task_difficulties[::step][:batch_size]
                ]
        
        # Ensure we don't exceed batch size
        selected_tasks = selected_tasks[:batch_size]
        
        # Log selection details
        self.logger.info(
            f"Selected {len(selected_tasks)} tasks for batch. "
            f"Current phase: {self.phase}, Success rate range: "
            f"[{self.current_min:.2f}, {self.current_max:.2f}]"
        )
        
        return selected_tasks
    
    def get_phase_info(self) -> Dict[str, Any]:
        """Get current phase information for logging and monitoring."""
        return {
            "phase": self.phase,
            "current_min_success_rate": self.current_min,
            "current_max_success_rate": self.current_max,
            "low_coverage_threshold": self.low_coverage_threshold,
            "expansion_rate": self.expansion_rate
        }


def main():
    """
    Main entry point for the curriculum scheduler.
    Demonstrates the two-phase logic with dynamic range expansion.
    """
    # Example configuration
    config = {
        "low_coverage_threshold": 0.05,
        "sweet_spot_min": 0.10,
        "sweet_spot_max": 0.90,
        "expansion_rate": 0.1,
        "phase_transition_threshold": 0.3
    }
    
    # Initialize scheduler
    scheduler = CurriculumScheduler(config)
    
    # Example tasks (in real usage, these would come from MobileGym)
    tasks = [
        {"id": "task_1", "coverage_vector": [1, 0, 0, 1]},
        {"id": "task_2", "coverage_vector": [0, 1, 1, 0]},
        {"id": "task_3", "coverage_vector": [1, 1, 0, 0]},
        {"id": "task_4", "coverage_vector": [0, 0, 1, 1]},
        {"id": "task_5", "coverage_vector": [1, 0, 1, 0]},
    ]
    
    # Example history (in real usage, this would come from previous rollouts)
    history = [
        {"task_id": "task_1", "success": True},
        {"task_id": "task_2", "success": False},
        {"task_id": "task_3", "success": True},
        {"task_id": "task_1", "success": True},
        {"task_id": "task_2", "success": True},
    ]
    
    # Example current coverage
    current_coverage = [0.2, 0.1, 0.3, 0.1]
    
    # Select tasks
    selected_tasks = scheduler.select_tasks(tasks, history, current_coverage, batch_size=3)
    
    # Log results
    print(f"Selected tasks: {[t['id'] for t in selected_tasks]}")
    print(f"Phase info: {scheduler.get_phase_info()}")
    
    # Demonstrate phase transition
    # Add more history to trigger Phase 2
    extended_history = history + [
        {"task_id": "task_4", "success": True},
        {"task_id": "task_5", "success": True},
        {"task_id": "task_3", "success": True},
        {"task_id": "task_1", "success": True},
        {"task_id": "task_2", "success": True},
    ]
    
    scheduler._update_phase(extended_history)
    print(f"After phase update: {scheduler.get_phase_info()}")
    
    # Select tasks again with updated phase
    selected_tasks_phase2 = scheduler.select_tasks(tasks, extended_history, current_coverage, batch_size=3)
    print(f"Phase 2 selected tasks: {[t['id'] for t in selected_tasks_phase2]}")


if __name__ == "__main__":
    main()