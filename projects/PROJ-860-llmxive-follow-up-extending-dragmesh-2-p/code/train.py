import os
import sys
import time
import json
import logging
import numpy as np

from estimator import VirtualTactileEstimator
from scheduler import AdaptiveRewardScheduler
from environment import PhysicsEnvironment, create_cpu_environment
from seed_config import set_seeds
from logging_config import setup_training_logger, get_logger

class AdaptiveTrainingLoop:
    """
    Implements the adaptive training loop for Virtual Tactile Zero-Shot Adaptation.
    Integrates VirtualTactileEstimator and AdaptiveRewardScheduler.
    """
    def __init__(self, env: PhysicsEnvironment, logger: logging.Logger = None):
        self.env = env
        self.logger = logger or setup_training_logger()
        self.estimator = VirtualTactileEstimator(window_size=5, epsilon=1e-4)
        self.scheduler = AdaptiveRewardScheduler()
        self.episode_log = []

    def reset_estimator(self):
        """Reset the estimator state for a new episode."""
        self.estimator.reset()
        self.scheduler.reset()

    def run_episode(self, max_steps: int = 1000, object_id: str = "unknown"):
        """
        Run a single training episode with adaptive reward scheduling.
        
        Args:
            max_steps: Maximum number of simulation steps.
            object_id: Identifier for the current object being manipulated.
        
        Returns:
            dict: Episode statistics including total reward, success flag, and k_est history.
        """
        self.reset_estimator()
        self.env.reset()
        
        total_reward = 0.0
        success = False
        k_est_history = []
        reward_weights_history = []
        
        # Initial state
        state = self.env.get_state()
        
        for step in range(max_steps):
            # 1. Estimate Virtual Tactile Stiffness (k_est)
            torque = state.get('torque', 0.0)
            velocity = state.get('velocity', 0.0)
            
            k_est = self.estimator.update(torque, velocity)
            k_est_history.append(k_est)
            
            # 2. Log k_est and current reward weights (T016b Requirement)
            current_weights = self.scheduler.get_current_weights()
            reward_weights_history.append(current_weights)
            
            self.logger.info(
                f"[Episode: {object_id}, Step: {step}] "
                f"k_est={k_est:.6f}, "
                f"Reward_Weights=detach:{current_weights['detach']:.4f}, "
                f"contact:{current_weights['contact']:.4f}"
            )

            # 3. Determine Action (Simple heuristic for this demo loop)
            # In a real RL setup, this would be a policy network inference.
            # Here we use a simple rule: if k_est is high (stiction/high friction), 
            # try to increase velocity to break stiction, else maintain.
            if k_est > 1.0:
                action = 0.5  # Push harder
            elif k_est < 0.2:
                action = 0.1  # Gentle touch
            else:
                action = 0.3  # Normal push
            
            # 4. Step Environment
            next_state, reward, done, info = self.env.step(action)
            
            # 5. Apply Adaptive Reward Scaling
            # The scheduler adjusts the raw reward based on k_est
            scaled_reward = self.scheduler.scale_reward(reward, k_est)
            
            total_reward += scaled_reward
            state = next_state
            
            if done:
                # Check success criteria (e.g., object moved past threshold)
                success = info.get('success', False)
                break
        
        episode_stats = {
            "object_id": object_id,
            "total_reward": total_reward,
            "success": success,
            "steps": step + 1,
            "k_est_final": k_est_history[-1] if k_est_history else 0.0,
            "k_est_mean": float(np.mean(k_est_history)) if k_est_history else 0.0,
            "k_est_max": float(np.max(k_est_history)) if k_est_history else 0.0,
            "k_est_min": float(np.min(k_est_history)) if k_est_history else 0.0,
            "reward_adjustments_applied": len(reward_weights_history)
        }
        
        self.logger.info(f"[Episode: {object_id}] Finished. Success: {success}, Total Reward: {total_reward:.4f}")
        return episode_stats

def run_episode(env, estimator, scheduler, max_steps=1000, logger=None):
    """
    Standalone function for running an episode (legacy compatibility).
    Delegates to AdaptiveTrainingLoop.
    """
    loop = AdaptiveTrainingLoop(env, logger)
    return loop.run_episode(max_steps)

def train(config: dict):
    """
    Main training function.
    
    Args:
        config: Dictionary containing training hyperparameters and paths.
    """
    logger = setup_training_logger()
    logger.info("Starting Adaptive Training Loop...")
    
    # Set seeds for reproducibility
    seed = config.get('seed', 42)
    set_seeds(seed)
    logger.info(f"Seeds set to {seed}")
    
    # Initialize Environment
    env = create_cpu_environment()
    
    # Initialize Training Loop
    trainer = AdaptiveTrainingLoop(env, logger)
    
    # Training Loop
    num_episodes = config.get('num_episodes', 50)
    max_steps = config.get('max_steps', 1000)
    
    results = []
    
    for ep_idx in range(num_episodes):
        # Generate a synthetic object ID for this run if not provided
        # In a full pipeline, this would load from data/generated/
        object_id = f"obj_train_{ep_idx:03d}"
        
        logger.info(f"--- Starting Episode {ep_idx + 1}/{num_episodes} ---")
        stats = trainer.run_episode(max_steps=max_steps, object_id=object_id)
        results.append(stats)
        
        # Log summary for the episode
        logger.info(
            f"Episode {ep_idx + 1} Summary: "
            f"Success={stats['success']}, "
            f"Mean k_est={stats['k_est_mean']:.4f}, "
            f"Max k_est={stats['k_est_max']:.4f}"
        )
    
    # Save results
    output_path = config.get('output_path', 'data/generated/training_results.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Training complete. Results saved to {output_path}")
    return results

def main():
    """Entry point for CLI execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Adaptive Training Loop")
    parser.add_argument('--num_episodes', type=int, default=10, help='Number of training episodes')
    parser.add_argument('--max_steps', type=int, default=500, help='Max steps per episode')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--output', type=str, default='data/generated/training_results.json', help='Output JSON path')
    
    args = parser.parse_args()
    
    config = {
        'num_episodes': args.num_episodes,
        'max_steps': args.max_steps,
        'seed': args.seed,
        'output_path': args.output
    }
    
    train(config)

if __name__ == "__main__":
    main()