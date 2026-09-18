"""
DOPD (Dynamic On-Policy Distillation) training implementation.
"""
import numpy as np
from typing import Tuple, Optional, Dict, Any, List
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env.privilege_mdp import PrivilegeMDP
from agents.teacher import TeacherOracle
from agents.student import TabularQStudent
from agents.baseline_estimator import BaselineEstimator
from utils.logging import TrainingLogger

class DOPDTrainer:
    def __init__(self, env: PrivilegeMDP, teacher: TeacherOracle, 
                 student: TabularQStudent, baseline_estimator: BaselineEstimator,
                 logger: TrainingLogger, discount_factor: float = 0.99):
        self.env = env
        self.teacher = teacher
        self.student = student
        self.baseline_estimator = baseline_estimator
        self.logger = logger
        self.discount_factor = discount_factor
        
        # Dynamic weighting parameters
        self.min_lambda = 0.1
        self.max_lambda = 1.0
        self.adaptive_threshold = 0.1
        
        # Rolling window for dynamic range calculation
        self.batch_size = 10
        self.rolling_advantage_gaps: List[float] = []

    def calculate_advantage_gap(self, state: int, action: int) -> float:
        """Calculate the advantage gap Q(s,a) - V_baseline(s)."""
        # Get Q-value from teacher's optimal policy (cached)
        q_value = self.teacher.get_q_value(state, action)
        
        # Get baseline value
        v_baseline = self.baseline_estimator.get_v_baseline(state)
        
        return q_value - v_baseline

    def calculate_dynamic_lambda(self, advantage_gap: float) -> float:
        """
        Calculate dynamic lambda based on advantage gap.
        Implements min-max normalization with fallback.
        """
        # Add to rolling window
        self.rolling_advantage_gaps.append(advantage_gap)
        if len(self.rolling_advantage_gaps) > self.batch_size:
            self.rolling_advantage_gaps.pop(0)
        
        # Check if we have enough data
        if len(self.rolling_advantage_gaps) < 2:
            return 1.0  # Default to uniform if not enough data
        
        # Calculate dynamic range
        min_gap = min(self.rolling_advantage_gaps)
        max_gap = max(self.rolling_advantage_gaps)
        dynamic_range = max_gap - min_gap
        
        # Check for min-max switch condition
        if dynamic_range < self.adaptive_threshold:
            # Trigger min-max normalization switch
            try:
                lambda_val = (advantage_gap - min_gap) / (dynamic_range + 1e-8)
            except ZeroDivisionError:
                lambda_val = 1.0  # Fallback to uniform
        else:
            # Use standard weighting based on gap magnitude
            # Normalize to [0, 1] range based on expected gap magnitude
            # Assuming typical gap range is roughly [0, 10]
            lambda_val = min(1.0, max(0.0, advantage_gap / 5.0))
        
        # Clamp to valid range
        lambda_val = max(self.min_lambda, min(self.max_lambda, lambda_val))
        
        return lambda_val

    def train_step(self, step: int) -> Dict[str, float]:
        """Execute a single training step."""
        # Get current state
        state = self.env.current_state
        
        # Get teacher action (optimal)
        teacher_action = self.teacher.select_action(state)
        
        # Calculate advantage gap
        advantage_gap = self.calculate_advantage_gap(state, teacher_action)
        
        # Calculate dynamic lambda
        lambda_weight = self.calculate_dynamic_lambda(advantage_gap)
        
        # Log lambda switch event if applicable
        if lambda_weight == 1.0 and advantage_gap < self.adaptive_threshold:
            log_entry = {
                "step": step,
                "event": "lambda_switch",
                "reason": "low_dynamic_range",
                "advantage_gap": advantage_gap
            }
            # Append to training log
            self._append_to_training_log(log_entry)
        
        # Student learns with weighted distillation
        # Execute action in environment
        next_state, reward, done, info = self.env.step(teacher_action)
        
        # Update student Q-table with weighted distillation loss
        # The loss is weighted by lambda_weight
        # For simplicity, we use a standard Q-learning update with a weighted learning rate
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
            "lambda_weight": lambda_weight,
            "advantage_gap": advantage_gap
        }

    def _calculate_entropy(self, action_probs: np.ndarray) -> float:
        """Calculate action entropy."""
        action_probs = np.clip(action_probs, 1e-10, 1.0)
        return -np.sum(action_probs * np.log(action_probs))

    def _append_to_training_log(self, entry: Dict[str, Any]):
        """Append an entry to the training log JSON file."""
        log_path = os.path.join("data", "raw", "training_log.json")
        
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                try:
                    log_data = json.load(f)
                except json.JSONDecodeError:
                    log_data = {"metadata": {}, "entries": []}
        else:
            log_data = {"metadata": {}, "entries": []}
        
        # Ensure entries list exists
        if "entries" not in log_data:
            log_data["entries"] = []
        
        # Add entry
        entry["timestamp"] = datetime.now().isoformat()
        log_data["entries"].append(entry)
        
        # Write back
        with open(log_path, 'w') as f:
            json.dump(log_data, f, indent=2)

def train_dopd(env: PrivilegeMDP, teacher: TeacherOracle, 
               student: TabularQStudent, baseline_estimator: BaselineEstimator,
               logger: TrainingLogger, total_steps: int, seed: int) -> Dict[str, Any]:
    """
    Train student using DOPD regime.
    
    Args:
        env: Environment instance.
        teacher: Teacher oracle agent.
        student: Student agent to train.
        baseline_estimator: Baseline value estimator.
        logger: Training logger instance.
        total_steps: Total number of training steps.
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary containing training results.
    """
    trainer = DOPDTrainer(env, teacher, student, baseline_estimator, logger)
    
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

def run_generalization_analysis(env: PrivilegeMDP, student: TabularQStudent,
                                teacher: TeacherOracle, num_episodes: int = 100) -> Dict[str, float]:
    """
    Run generalization analysis by evaluating student performance.
    
    Args:
        env: Environment instance.
        student: Trained student agent.
        teacher: Teacher oracle for comparison.
        num_episodes: Number of evaluation episodes.
        
    Returns:
        Dictionary containing generalization metrics.
    """
    total_reward = 0
    total_teacher_reward = 0
    correct_actions = 0
    
    for _ in range(num_episodes):
        state = env.reset()
        done = False
        
        while not done:
            # Student action
            student_action = student.select_action(state, training=False)
            next_state, reward, done, info = env.step(student_action)
            total_reward += reward
            
            # Teacher action for comparison
            teacher_action = teacher.select_action(state)
            if student_action == teacher_action:
                correct_actions += 1
            
            state = next_state
            
            # Get teacher reward for same state
            # (This is a simplified approximation)
            _, teacher_reward, _, _ = env.step(teacher_action)
            total_teacher_reward += teacher_reward
    
    accuracy = correct_actions / (num_episodes * env.max_steps_per_episode)
    performance_ratio = total_reward / (total_teacher_reward + 1e-8)
    
    return {
        "generalization_accuracy": accuracy,
        "performance_ratio": performance_ratio,
        "student_total_reward": total_reward,
        "teacher_total_reward": total_teacher_reward
    }
