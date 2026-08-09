"""
Simulated Student Model for ZPPO Simulation.

This module implements the `SimulatedStudent` class which models a student agent
learning from a teacher via Negative Candidate-included Question (NCQ) prompts.
It tracks confidence scores for tasks and updates them based on the "expert gap"
(difference between expert confidence and student confidence) and the specific
learning dynamics of the ZPPO protocol.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from utils.logging import get_logger, info, debug, warning
from utils.seeds import get_rng
from config import get_config

logger = get_logger(__name__)


class SimulatedStudent:
    """
    A simulated student model that updates confidence scores based on
    the gap between student and expert performance on specific tasks.

    Attributes:
        tasks (Dict[str, Dict]): Dictionary mapping task IDs to their state.
            Each state contains:
            - 'expert_confidence': float (0.0 to 1.0)
            - 'student_confidence': float (0.0 to 1.0)
            - 'ground_truth': bool (whether the student eventually gets it right)
            - 'history': List[float] (record of student confidence over cycles)
        learning_rate (float): Base learning rate for confidence updates.
        noise_scale (float): Standard deviation for Gaussian noise injection (FR-008).
        cycle_count (int): Current training cycle counter.
    """

    def __init__(
        self,
        initial_tasks: Optional[List[Dict[str, Any]]] = None,
        learning_rate: float = 0.1,
        noise_scale: float = 0.05,
        seed: Optional[int] = None
    ):
        """
        Initialize the SimulatedStudent.

        Args:
            initial_tasks: List of task dictionaries with 'id', 'expert_confidence',
                           'ground_truth', and optionally 'initial_student_confidence'.
            learning_rate: The rate at which confidence updates occur.
            noise_scale: Sigma for Gaussian noise injection (FR-008).
            seed: Random seed for reproducibility. If None, uses global seed.
        """
        self.learning_rate = learning_rate
        self.noise_scale = noise_scale
        self.cycle_count = 0
        self.tasks: Dict[str, Dict[str, Any]] = {}

        # Initialize RNG
        if seed is not None:
            self.rng = np.random.default_rng(seed)
        else:
            self.rng = get_rng()

        if initial_tasks:
            self._load_tasks(initial_tasks)
        else:
            logger.warning("SimulatedStudent initialized with no tasks.")

    def _load_tasks(self, tasks: List[Dict[str, Any]]) -> None:
        """
        Load initial task states from a list of dictionaries.

        Args:
            tasks: List of task definitions.
        """
        for task in tasks:
            task_id = task['id']
            expert_conf = float(task['expert_confidence'])
            ground_truth = task.get('ground_truth', True)
            # Default initial student confidence to 0.5 if not provided,
            # or use the provided value clamped to [0, 1].
            initial_student_conf = task.get('initial_student_confidence', 0.5)
            initial_student_conf = float(initial_student_conf)
            initial_student_conf = np.clip(initial_student_conf, 0.0, 1.0)

            self.tasks[task_id] = {
                'expert_confidence': expert_conf,
                'student_confidence': initial_student_conf,
                'ground_truth': ground_truth,
                'history': [initial_student_conf],
                'pruned': False, # Tracks if this task was pruned by CAP
                'rejected_count': 0, # For CAP logic tracking
                'accepted_count': 0
            }
            debug(f"Loaded task {task_id}: Expert={expert_conf:.3f}, Student={initial_student_conf:.3f}")

    def get_task_confidence(self, task_id: str) -> float:
        """Get current student confidence for a specific task."""
        if task_id not in self.tasks:
            raise KeyError(f"Task {task_id} not found in student model.")
        return self.tasks[task_id]['student_confidence']

    def get_all_confidences(self) -> Dict[str, float]:
        """Get current student confidence for all tasks."""
        return {tid: t['student_confidence'] for tid, t in self.tasks.items()}

    def calculate_expert_gap(self, task_id: str) -> float:
        """
        Calculate the gap between expert and student confidence.
        Gap = Expert - Student. Positive gap implies room for improvement.
        """
        if task_id not in self.tasks:
            raise KeyError(f"Task {task_id} not found.")
        task = self.tasks[task_id]
        return task['expert_confidence'] - task['student_confidence']

    def update_confidence(
        self,
        task_id: str,
        feedback_type: str,
        noise_inject: bool = True
    ) -> float:
        """
        Update the student's confidence for a task based on feedback.

        This implements the core ZPPO learning dynamic:
        - If the student is in the "Zone of Proximal" (gap is significant but not impossible),
          confidence increases.
        - If the student is already high confidence, updates are dampened.
        - If the student is very low confidence (consistently rejected), updates might be negative
          or stagnant depending on the feedback type.

        Args:
            task_id: The ID of the task to update.
            feedback_type: One of 'success', 'failure', 'partial'.
            noise_inject: Whether to inject Gaussian noise (FR-008).

        Returns:
            The new confidence score.
        """
        if task_id not in self.tasks:
            raise KeyError(f"Task {task_id} not found.")

        task = self.tasks[task_id]
        current_conf = task['student_confidence']
        expert_conf = task['expert_confidence']
        gap = expert_conf - current_conf

        # Base update logic based on feedback type
        delta = 0.0
        if feedback_type == 'success':
            # If successful, move towards expert confidence
            # The update is proportional to the gap (learning from the gap)
            delta = self.learning_rate * gap
        elif feedback_type == 'failure':
            # If failure, confidence drops, but not below 0.
            # The drop is also proportional to the gap (if gap is large, we are far from expert,
            # so failure confirms low confidence; if gap is small, failure is surprising).
            # However, in ZPPO, failure on a negative candidate is expected.
            # We simulate a small decrease if the student was overconfident relative to the negative candidate.
            # For this simulation, we assume 'failure' on a negative candidate means the student
            # correctly identified it as wrong, so confidence in the *correct* answer (expert) might not drop,
            # but here we are modeling the confidence in the *task* (solving it correctly).
            # If the student fails the task, confidence drops.
            delta = -self.learning_rate * (1.0 - current_conf) * 0.5
        elif feedback_type == 'partial':
            # Partial credit: small positive update
            delta = self.learning_rate * gap * 0.5
        else:
            warning(f"Unknown feedback type: {feedback_type}")

        # Apply noise injection (FR-008)
        if noise_inject and self.noise_scale > 0:
            noise = self.rng.normal(0.0, self.noise_scale)
            delta += noise

        new_conf = current_conf + delta

        # Clamp to [0, 1]
        new_conf = float(np.clip(new_conf, 0.0, 1.0))

        # Update state
        task['student_confidence'] = new_conf
        task['history'].append(new_conf)

        debug(f"Task {task_id}: Conf {current_conf:.3f} -> {new_conf:.3f} (Gap: {gap:.3f}, Delta: {delta:.3f})")

        return new_conf

    def simulate_buffer_cycle(
        self,
        active_task_ids: List[str],
        feedback_map: Dict[str, str]
    ) -> Dict[str, float]:
        """
        Simulate a single buffer cycle where the student attempts a set of tasks.

        Args:
            active_task_ids: List of task IDs the student is attempting in this cycle.
            feedback_map: Dictionary mapping task_id to feedback type ('success', 'failure', etc.).

        Returns:
            Dictionary of task_id -> new confidence.
        """
        results = {}
        self.cycle_count += 1

        for task_id in active_task_ids:
            if task_id not in self.tasks:
                continue

            feedback = feedback_map.get(task_id, 'failure')
            new_conf = self.update_confidence(task_id, feedback)
            results[task_id] = new_conf

        return results

    def get_accuracy(self, threshold: float = 0.9) -> float:
        """
        Calculate the current accuracy of the student.
        Accuracy is defined as the fraction of tasks where student_confidence >= threshold.

        Args:
            threshold: Confidence threshold to consider a task "solved".

        Returns:
            Accuracy score (0.0 to 1.0).
        """
        if not self.tasks:
            return 0.0

        solved_count = sum(
            1 for t in self.tasks.values()
            if t['student_confidence'] >= threshold
        )
        return solved_count / len(self.tasks)

    def get_convergence_data(self) -> List[Dict[str, Any]]:
        """
        Get the full history of confidence scores for all tasks.

        Returns:
            List of dicts with 'task_id', 'cycle', 'confidence'.
        """
        data = []
        max_cycles = max(len(t['history']) for t in self.tasks.values()) if self.tasks else 0

        for task_id, task in self.tasks.items():
            for cycle_idx, conf in enumerate(task['history']):
                data.append({
                    'task_id': task_id,
                    'cycle': cycle_idx,
                    'confidence': conf
                })
        return data

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get summary metrics for the current state.

        Returns:
            Dictionary with 'accuracy', 'mean_confidence', 'tasks_solved'.
        """
        if not self.tasks:
            return {
                'accuracy': 0.0,
                'mean_confidence': 0.0,
                'tasks_solved': 0,
                'total_tasks': 0
            }

        confidences = [t['student_confidence'] for t in self.tasks.values()]
        accuracy = self.get_accuracy()

        return {
            'accuracy': accuracy,
            'mean_confidence': float(np.mean(confidences)),
            'std_confidence': float(np.std(confidences)),
            'tasks_solved': sum(1 for c in confidences if c >= 0.9),
            'total_tasks': len(self.tasks)
        }