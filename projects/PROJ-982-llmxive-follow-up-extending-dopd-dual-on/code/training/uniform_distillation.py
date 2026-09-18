"""
Uniform On-Policy Distillation training implementation.
"""
import numpy as np
from typing import Tuple, Optional, Dict, Any, List
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env.privilege_mdp import PrivilegeMDP
from agents.teacher import TeacherOracle
from agents.student import TabularQStudent
from agents.baseline_estimator import BaselineEstimator
from utils.logging import TrainingLogger

class UniformDistillationTrainer:
    def __init__(self, env: PrivilegeMDP, teacher: TeacherOracle, 
                 student: TabularQStudent, logger: TrainingLogger,
                 discount_factor: float = 0.99, fixed_weight: float = 1.0):
        self.env = env
        self.teacher = teacher
        self.student = student
        self.logger = logger
        self.discount_factor = discount_factor
        self.fixed_weight = fixed_weight

    def train_step(self, step: int) -> Dict[str, float]:
        """Execute a single training step with uniform weighting."""
        # Get current state
        state = self.env.current_state
        
        # Get teacher action (optimal)
        teacher_action = self.teacher.select_action(state)
        
        # Uniform weighting: always use fixed weight
        lambda_weight = self.fixed_weight
        
        # Student learns with uniform distillation
        # Execute action in environment
        next_state, reward, done, info = self.env.step(teacher_action)
        
        # Update student Q-table with uniform learning rate
        effective_lr = self.student.learning_rate * lambda_weight
        self.student.update_q_table(state, teacher_action, reward, next_state, effective_lr)
        
        # Calculate metrics
        # Simple accuracy: does student choose teacher action?
        student_action = self.student.select_action(state, training=False)
        accuracy = 1.0 if student_action == teacher_action else 0.0
        
        # Calculate entropy
        action_probs = self.student.get_action_probs(state)
        entropy = self._calculate_entropy(action_probs)
        
        # Calculate loss (simplified: negative reward)
        loss = -reward
        
        # Log metrics
        self.logger.log_step(step, reward, loss, accuracy, entropy)
        
        return {
            "reward": reward,
            "loss": loss,
            "accuracy": accuracy,
            "entropy": entropy,
            "lambda_weight": lambda_weight
        }

    def _calculate_entropy(self, action_probs: np.ndarray) -> float:
        """Calculate action entropy."""
        action_probs = np.clip(action_probs, 1e-10, 1.0)
        return -np.sum(action_probs * np.log(action_probs))

def train_uniform(env: PrivilegeMDP, teacher: TeacherOracle, 
                  student: TabularQStudent, baseline_estimator: Optional[BaselineEstimator],
                  logger: TrainingLogger, total_steps: int, seed: int) -> Dict[str, Any]:
    """
    Train student using Uniform distillation regime.
    
    Args:
        env: Environment instance.
        teacher: Teacher oracle agent.
        student: Student agent to train.
        baseline_estimator: Baseline value estimator (unused in uniform regime).
        logger: Training logger instance.
        total_steps: Total number of training steps.
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary containing training results.
    """
    trainer = UniformDistillationTrainer(env, teacher, student, logger)
    
    # Reset environment
    state = env.reset(seed=seed)
    
    results = {
        "steps": [],
        "rewards": [],
        "losses": [],
        "accuracies": [],
        "entropies": [],
        "lambda_weights": []
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
            state = env.reset(seed=seed + step)  # Reset with new seed
        
        # Periodic logging could be added here
        
    return results
