"""
Training loop runner for TOP-D policy distillation.

This module implements the main training loop that coordinates the interaction
between the student policy, teacher policy, and TOP-D loss function.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd

# Add project root to path for imports if running from tests
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root / "code"))

from utils.seed_manager import set_seed, get_seed
from utils.logger import get_logger
from env.reasoning_mdp import ReasoningMDP, State, Action
from env.teacher_policy import TeacherPolicy
from student.policy import StudentPolicy
from student.topd_loss import TOPDLoss

logger = get_logger(__name__)

def run_training_loop(
    mdp: ReasoningMDP,
    teacher_policy: TeacherPolicy,
    student_policy: StudentPolicy,
    loss_fn: TOPDLoss,
    alpha: float,
    num_episodes: int,
    max_steps: int,
    log_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Run the TOP-D training loop for a specified number of episodes.
    
    Args:
        mdp: The Reasoning MDP environment
        teacher_policy: The teacher policy providing optimal actions
        student_policy: The student policy being trained
        loss_fn: The TOP-D loss function for computing gradients
        alpha: Interpolation coefficient (0.0 = pure student, 1.0 = pure teacher)
        num_episodes: Number of training episodes
        max_steps: Maximum steps per episode
        log_path: Optional path to write episode logs (CSV)
    
    Returns:
        List of dictionaries containing episode statistics
    """
    if not (0.0 <= alpha <= 1.0):
        raise ValueError(f"Alpha must be between 0.0 and 1.0, got {alpha}")
    
    history = []
    episode_logs = []
    
    logger.info(f"Starting training loop: alpha={alpha}, episodes={num_episodes}, "
                f"max_steps={max_steps}")
    
    for episode in range(num_episodes):
        # Reset environment
        state = mdp.reset()
        done = False
        step = 0
        episode_loss = 0.0
        effective_depth = 0
        teacher_depth = 0
        
        while not done and step < max_steps:
            # Get teacher action (optimal)
            teacher_action = teacher_policy.get_action(state)
            
            # Get student action
            student_action = student_policy.get_action(state)
            
            # Compute TOP-D loss
            loss_value = loss_fn.compute_loss(
                state=state,
                teacher_action=teacher_action,
                student_action=student_action,
                alpha=alpha
            )
            
            # Update student policy (simplified gradient step)
            student_policy.update(loss_value, alpha)
            
            # Execute student action in environment
            next_state, reward, done, info = mdp.step(student_action)
            
            # Track depths
            effective_depth = info.get("effective_depth", step + 1)
            teacher_depth = info.get("teacher_depth", step + 1)
            
            episode_loss += loss_value
            state = next_state
            step += 1
        
        # Record episode statistics
        episode_stats = {
            "episode": episode,
            "loss": episode_loss / max(step, 1),
            "effective_depth": effective_depth,
            "teacher_depth": teacher_depth,
            "collapse_ratio": effective_depth / max(teacher_depth, 1),
            "alpha": alpha,
            "horizon": student_policy.horizon,
            "steps": step
        }
        
        history.append(episode_stats)
        episode_logs.append(episode_stats)
        
        # Log progress every 10 episodes
        if (episode + 1) % 10 == 0:
            avg_loss = np.mean([h["loss"] for h in history[-10:]])
            logger.info(f"Episode {episode + 1}/{num_episodes}: "
                        f"Avg Loss={avg_loss:.4f}, "
                        f"Eff Depth={effective_depth}, "
                        f"Teacher Depth={teacher_depth}")
    
    # Write logs to CSV if path provided
    if log_path:
        log_file = Path(log_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(episode_logs)
        df.to_csv(log_file, index=False)
        logger.info(f"Episode logs written to {log_file}")
    
    return history
