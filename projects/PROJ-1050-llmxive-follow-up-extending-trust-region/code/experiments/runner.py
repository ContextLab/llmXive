"""
Training Loop Runner for TOP-D Distillation.

Executes the training loop for a given GridConfig, handling the interaction
between the StudentPolicy, TeacherPolicy, and the ReasoningMDP environment.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
import csv

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import get_logger
from utils.seed_manager import set_seed
from env.reasoning_mdp import ReasoningMDP
from env.teacher_policy import TeacherPolicy
from student.policy import StudentPolicy
from student.topd_loss import TOPDLoss
from experiments.grid_config import GridConfig

def run_training_loop(config: GridConfig) -> Optional[Dict[str, Any]]:
    """
    Run the training loop for a single configuration.

    Args:
        config: GridConfig containing hyperparameters for this run.

    Returns:
        Dictionary containing aggregated metrics (avg_loss, collapse_ratio, etc.)
        or None if execution fails.
    """
    logger = get_logger("training_runner")
    logger.info(f"Starting training loop for config: alpha={config.alpha}, "
                f"horizon={config.student_horizon}, episodes={config.num_episodes}")

    try:
        set_seed(config.seed)

        # Initialize Environment and Policies
        env = ReasoningMDP(size=config.env_size)
        teacher = TeacherPolicy(env)
        student = StudentPolicy(env, horizon_limit=config.student_horizon)
        loss_fn = TOPDLoss(alpha=config.alpha)

        # Metrics tracking
        episode_losses = []
        effective_depths = []
        teacher_depths = []
        collapse_counts = 0
        total_steps = 0

        # Prepare log file
        log_path = Path(config.output_dir) / config.log_file_name
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Training Loop
        for episode in range(config.num_episodes):
            state = env.reset()
            episode_loss = 0.0
            step_count = 0
            actual_depth = 0
            teacher_plan = []

            while not env.done:
                # Teacher generates optimal plan (limited by max horizon for efficiency)
                if not teacher_plan:
                    teacher_plan = teacher.get_plan(state, max_steps=config.teacher_horizon)
                
                # Get student action
                student_action = student.select_action(state)
                
                # Get teacher action (from plan)
                teacher_action = teacher_plan[0] if teacher_plan else None
                
                if teacher_action is None:
                    # Fallback if plan exhausted
                    teacher_action = teacher.get_action(state)

                # Step environment
                next_state, reward, done, info = env.step(student_action)
                actual_depth += 1
                step_count += 1

                # Calculate TOP-D Loss
                # We need to simulate the probability distribution for the loss calculation
                # In a real implementation, StudentPolicy would return a distribution
                student_dist = student.get_action_distribution(state)
                teacher_dist = np.zeros_like(student_dist)
                if teacher_action is not None:
                    teacher_dist[teacher_action] = 1.0
                
                loss = loss_fn(student_dist, teacher_dist)
                episode_loss += loss

                state = next_state
                if done:
                    break

                # Safety break
                if step_count > config.max_steps_per_episode:
                    break

            # Episode Summary
            episode_losses.append(episode_loss)
            effective_depths.append(actual_depth)
            teacher_depths.append(len(teacher_plan))
            total_steps += step_count

            # Collapse detection: effective depth <= 0.5 * teacher depth
            if len(teacher_plan) > 0:
                if actual_depth <= 0.5 * len(teacher_plan):
                    collapse_counts += 1

            # Log per episode
            with open(log_path, 'a', newline='') as f:
                writer = csv.writer(f)
                if episode == 0:
                    writer.writerow(['episode', 'loss', 'effective_depth', 'teacher_depth', 'collapse'])
                writer.writerow([episode, episode_loss, actual_depth, len(teacher_plan), 
                                 1 if actual_depth <= 0.5 * len(teacher_plan) else 0])

        # Calculate aggregated metrics
        avg_loss = float(np.mean(episode_losses))
        avg_eff_depth = float(np.mean(effective_depths))
        avg_teacher_depth = float(np.mean(teacher_depths))
        collapse_ratio = collapse_counts / config.num_episodes
        
        # Convergence stability check (variance of loss)
        loss_variance = float(np.var(episode_losses))
        convergence_stable = loss_variance < 0.5 # Threshold heuristic

        result = {
            "avg_loss": avg_loss,
            "avg_effective_depth": avg_eff_depth,
            "avg_teacher_depth": avg_teacher_depth,
            "collapse_ratio": collapse_ratio,
            "collapse_count": collapse_counts,
            "total_steps": total_steps,
            "convergence_stable": convergence_stable,
            "loss_variance": loss_variance
        }

        logger.info(f"Training complete. Avg Loss: {avg_loss:.4f}, "
                    f"Collapse Ratio: {collapse_ratio:.4f}")
        return result

    except Exception as e:
        logger.error(f"Training loop failed: {e}", exc_info=True)
        return None
