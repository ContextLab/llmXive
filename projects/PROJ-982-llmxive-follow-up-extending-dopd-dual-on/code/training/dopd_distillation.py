"""
DOPD (Dynamic On‑Policy Distillation) training implementation.

Adjustments:
* Logs a ``lambda_switch`` event to the legacy ``training_log.json`` file
  when the dynamic λ falls back to the default (λ = 1.0) because the
  advantage‑gap range is too small.
* Uses the shared utilities ``calculate_advantage_gap`` and
  ``calculate_dynamic_lambda``.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List

import numpy as np

from ..env.privilege_mdp import PrivilegeMDP
from ..agents.baseline_estimator import BaselineEstimator
from ..agents.student import TabularQStudent
from ..agents.teacher import TeacherOracle
from ..utils.logging import TrainingLogger
from .utils import calculate_advantage_gap, calculate_dynamic_lambda


class DOPDTrainer:
    """
    Encapsulates a single DOPD training run.

    The trainer maintains a rolling window of advantage‑gap values to
    compute a dynamic λ weighting.  All per‑step metrics are logged via
    ``TrainingLogger``; λ‑switch events are also logged as structured
    entries in ``training_log.json``.
    """

    def __init__(
        self,
        env: PrivilegeMDP,
        teacher: TeacherOracle,
        student: TabularQStudent,
        baseline_estimator: BaselineEstimator,
        logger: TrainingLogger,
        discount_factor: float = 0.99,
    ) -> None:
        self.env = env
        self.teacher = teacher
        self.student = student
        self.baseline_estimator = baseline_estimator
        self.logger = logger
        self.discount_factor = discount_factor

        # Parameters for the dynamic λ computation.
        self.batch_size = 10
        self.rolling_advantage_gaps: List[float] = []

    # ------------------------------------------------------------------
    # Core calculations (delegated to ``training.utils``)
    # ------------------------------------------------------------------
    def _advantage_gap(self, state: tuple[int, int, int], action: int) -> float:
        """Thin wrapper around the shared utility."""
        return calculate_advantage_gap(self.teacher, self.baseline_estimator, state, action)

    def _dynamic_lambda(self, advantage_gap: float) -> float:
        """Thin wrapper around the shared utility."""
        # Update the rolling window.
        self.rolling_advantage_gaps.append(advantage_gap)
        if len(self.rolling_advantage_gaps) > self.batch_size:
            self.rolling_advantage_gaps.pop(0)

        return calculate_dynamic_lambda(self.rolling_advantage_gaps)

    # ------------------------------------------------------------------
    # Training step
    # ------------------------------------------------------------------
    def train_step(self, step: int) -> Dict[str, float]:
        """
        Execute a single training step.

        Returns a dictionary of the metrics that were logged; the dictionary
        is useful for the caller’s aggregation logic.
        """
        # Current full state (x, y, h) – the environment keeps it in
        # ``current_state``.
        state = self.env.current_state

        # Teacher provides the optimal action for the full state.
        teacher_action = self.teacher.select_action(state)

        # Compute the advantage gap and the dynamic λ.
        advantage_gap = self._advantage_gap(state, teacher_action)
        lambda_weight = self._dynamic_lambda(advantage_gap)

        # Log a lambda‑switch event if we fell back to the default λ.
        if lambda_weight == 1.0 and advantage_gap < 0.1:
            # Structured event written to the legacy JSON file.
            switch_entry = {
                "lambda_switch": "fallback",
                "step": step,
                "advantage_gap": advantage_gap,
                "timestamp": datetime.now().isoformat(),
            }
            # Record the event via the logger’s helper.
            self.logger.log_event(switch_entry)

        # Execute the teacher’s action in the environment.
        next_state, reward, done, _ = self.env.step(teacher_action)

        # Update the student using a weighted learning rate.
        effective_lr = self.student.learning_rate * lambda_weight
        self.student.update_q_table(
            state, teacher_action, reward, next_state, effective_lr
        )

        # Metrics for this step.
        student_action = self.student.select_action(state, training=False)
        accuracy = 1.0 if student_action == teacher_action else 0.0
        action_probs = self.student.get_action_probs(state)
        entropy = self._calculate_entropy(action_probs)
        loss = -reward  # simplified loss definition

        # Log the standard step metrics to the JSON‑Lines file.
        self.logger.log_step(
            step=step,
            reward=reward,
            loss=loss,
            accuracy=accuracy,
            entropy=entropy,
        )

        return {
            "reward": reward,
            "loss": loss,
            "accuracy": accuracy,
            "entropy": entropy,
            "lambda_weight": lambda_weight,
            "advantage_gap": advantage_gap,
            "done": done,
        }

    @staticmethod
    def _calculate_entropy(action_probs: np.ndarray) -> float:
        """Numerically stable entropy calculation."""
        probs = np.clip(action_probs, 1e-10, 1.0)
        return -float(np.sum(probs * np.log(probs)))


def train_dopd(
    env: PrivilegeMDP,
    teacher: TeacherOracle,
    student: TabularQStudent,
    baseline_estimator: BaselineEstimator,
    logger: TrainingLogger,
    total_steps: int,
    seed: int,
) -> Dict[str, Any]:
    """
    Convenience function used by ``code.main``.

    It creates a :class:`DOPDTrainer` instance, resets the environment,
    runs the training loop and returns a dictionary containing the
    per‑step histories.
    """
    trainer = DOPDTrainer(
        env, teacher, student, baseline_estimator, logger
    )

    # Reset the environment to a deterministic start state.
    env.reset(seed=seed)

    results: Dict[str, List[Any]] = {
        "steps": [],
        "rewards": [],
        "losses": [],
        "accuracies": [],
        "entropies": [],
        "lambda_weights": [],
    }

    for step in range(total_steps):
        metrics = trainer.train_step(step)

        results["steps"].append(step)
        results["rewards"].append(metrics["reward"])
        results["losses"].append(metrics["loss"])
        results["accuracies"].append(metrics["accuracy"])
        results["entropies"].append(metrics["entropy"])
        results["lambda_weights"].append(metrics["lambda_weight"])

        if metrics.get("done", False):
            # Episode finished – reset with a new seed to keep trajectories
            # distinct across resets.
            env.reset(seed=seed + step)

    return results


def run_generalization_analysis(
    env: PrivilegeMDP,
    student: TabularQStudent,
    teacher: TeacherOracle,
    num_episodes: int = 100,
) -> Dict[str, float]:
    """
    Evaluate the trained student against the teacher under masked
    observation (the privileged variable ``h`` is hidden from the student).

    The implementation mirrors the original version but now uses the
    public ``select_action`` API of both agents.
    """
    total_reward = 0.0
    total_teacher_reward = 0.0
    correct_actions = 0

    for _ in range(num_episodes):
        state = env.reset()
        done = False

        while not done:
            # Student acts based on its observable state.
            student_action = student.select_action(state, training=False)
            next_state, reward, done, _ = env.step(student_action)
            total_reward += reward

            # Teacher’s optimal action for the *same* full state.
            teacher_action = teacher.select_action(state)
            if student_action == teacher_action:
                correct_actions += 1

            # Collect teacher reward for the same transition (used for
            # performance ratio).
            _, teacher_reward, _, _ = env.step(teacher_action)
            total_teacher_reward += teacher_reward

            state = next_state

    # Normalise accuracy by the maximum possible number of actions.
    max_steps = env.max_steps_per_episode * num_episodes
    accuracy = correct_actions / max_steps
    performance_ratio = total_reward / (total_teacher_reward + 1e-8)

    return {
        "generalization_accuracy": accuracy,
        "performance_ratio": performance_ratio,
        "student_total_reward": total_reward,
        "teacher_total_reward": total_teacher_reward,
    }
