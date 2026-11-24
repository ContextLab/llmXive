"""
Uniform On‑Policy Distillation training implementation.

No functional changes were required for T003 beyond ensuring that the
module imports the (now external) ``TrainingLogger`` and that the logger
writes to the JSON‑Lines file defined by the logger itself.
"""
import numpy as np
from typing import Any, Dict, List

from env.privilege_mdp import PrivilegeMDP
from agents.baseline_estimator import BaselineEstimator
from agents.student import TabularQStudent
from agents.teacher import TeacherOracle
from utils.logging import TrainingLogger

class UniformDistillationTrainer:
    """
    Simple wrapper that always uses a fixed λ = 1.0.
    """

    def __init__(
        self,
        env: PrivilegeMDP,
        teacher: TeacherOracle,
        student: TabularQStudent,
        logger: TrainingLogger,
        discount_factor: float = 0.99,
        fixed_weight: float = 1.0,
    ) -> None:
        self.env = env
        self.teacher = teacher
        self.student = student
        self.logger = logger
        self.discount_factor = discount_factor
        self.fixed_weight = fixed_weight

    def train_step(self, step: int) -> Dict[str, float]:
        """Execute a single training step with uniform weighting."""
        state = self.env.current_state
        teacher_action = self.teacher.select_action(state)

        lambda_weight = self.fixed_weight

        next_state, reward, done, _ = self.env.step(teacher_action)

        effective_lr = self.student.learning_rate * lambda_weight
        self.student.update_q_table(state, teacher_action, reward, next_state, effective_lr)

        student_action = self.student.select_action(state, training=False)
        accuracy = 1.0 if student_action == teacher_action else 0.0

        action_probs = self.student.get_action_probs(state)
        entropy = self._calculate_entropy(action_probs)

        loss = -reward

        self.logger.log_step(step, reward, loss, accuracy, entropy)

        return {
            "reward": reward,
            "loss": loss,
            "accuracy": accuracy,
            "entropy": entropy,
            "lambda_weight": lambda_weight,
        }

    @staticmethod
    def _calculate_entropy(action_probs: np.ndarray) -> float:
        """Numerically stable entropy calculation."""
        probs = np.clip(action_probs, 1e-10, 1.0)
        return -float(np.sum(probs * np.log(probs)))

def train_uniform(
    env: PrivilegeMDP,
    teacher: TeacherOracle,
    student: TabularQStudent,
    baseline_estimator: BaselineEstimator | None,
    logger: TrainingLogger,
    total_steps: int,
    seed: int,
) -> Dict[str, Any]:
    """
    Convenience function used by ``code.main``.
    """
    trainer = UniformDistillationTrainer(env, teacher, student, logger)

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
            env.reset(seed=seed + step)

    return results
