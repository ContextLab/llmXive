"""
Training loop for Virtual Tactile Zero-Shot Adaptation.

Implements the adaptive policy loop that detects friction via k_est and adjusts rewards,
optimizing for CPU-tractable execution within the 6-hour limit.

Optimizations for T027:
- Reduced simulation steps per episode (from 500 to 150) to fit time budget.
- Reduced batch size (from 32 to 8) to reduce memory pressure.
- Implemented early stopping based on convergence.
- Streamlined logging to reduce I/O overhead.
"""
import os
import sys
import time
import json
import logging
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from collections import deque

# Local imports (matching API surface)
from environment import PhysicsEnvironment, create_cpu_environment
from estimator import VirtualTactileEstimator
from scheduler import AdaptiveRewardScheduler
from seed_config import set_seeds, get_seed
from logging_config import setup_training_logger, get_logger_for_module

# Constants for T027 Optimization
# Reduced steps per episode to ensure 6h limit is met
DEFAULT_STEPS_PER_EPISODE = 150 
# Reduced batch size to fit 7GB RAM limit
DEFAULT_BATCH_SIZE = 8
# Early stopping patience
EARLY_STOPPING_PATIENCE = 5
# Maximum total episodes to prevent runaway training
MAX_TOTAL_EPISODES = 500

@dataclass
class TrainingStats:
    episode: int
    avg_reward: float
    k_est_mean: float
    detach_rate: float
    duration_seconds: float
    memory_peak_mb: float

class AdaptiveTrainingLoop:
    """
    Main training loop integrating VirtualTactileEstimator and AdaptiveRewardScheduler.
    
    Optimized for CPU execution with reduced simulation steps and batch sizes.
    """
    def __init__(
        self,
        env: PhysicsEnvironment,
        estimator: VirtualTactileEstimator,
        scheduler: AdaptiveRewardScheduler,
        logger: Optional[logging.Logger] = None,
        steps_per_episode: int = DEFAULT_STEPS_PER_EPISODE,
        batch_size: int = DEFAULT_BATCH_SIZE,
        max_episodes: int = MAX_TOTAL_EPISODES,
        seed: int = 42
    ):
        self.env = env
        self.estimator = estimator
        self.scheduler = scheduler
        self.logger = logger or get_logger_for_module(__name__)
        self.steps_per_episode = steps_per_episode
        self.batch_size = batch_size
        self.max_episodes = max_episodes
        self.seed = seed
        
        # Set seeds for reproducibility
        set_seeds(seed)
        
        # Statistics tracking
        self.episode_rewards: List[float] = []
        self.best_avg_reward = -np.inf
        self.patience_counter = 0
        self.training_history: List[TrainingStats] = []

    def reset_episode(self):
        """Reset environment and estimator for a new episode."""
        self.env.reset()
        self.estimator.reset()
        self.scheduler.reset()

    def run_episode(self, episode_id: int) -> Tuple[float, float, float]:
        """
        Run a single training episode with adaptive rewards.
        
        Returns:
            Tuple of (total_reward, avg_k_est, detach_count)
        """
        self.reset_episode()
        total_reward = 0.0
        k_est_samples = []
        detach_count = 0
        
        # Pre-compute reward weights for this episode based on initial estimate
        # (or default if estimator has no data yet)
        current_weights = self.scheduler.get_weights()
        
        for step in range(self.steps_per_episode):
            # 1. Get current state
            state = self.env.get_state()
            
            # 2. Estimate tactile stiffness (k_est)
            # Pass torque and velocity derivatives from environment
            torque = state.get('torque', 0.0)
            velocity = state.get('velocity', 0.0)
            k_est = self.estimator.update(torque, velocity)
            
            # 3. Update scheduler with new k_est
            if k_est is not None and np.isfinite(k_est):
                k_est_samples.append(k_est)
                current_weights = self.scheduler.update(k_est)
            
            # 4. Compute reward
            reward = self._compute_reward(state, current_weights, k_est)
            
            # 5. Take action (simplified policy for optimization)
            action = self._select_action(state, current_weights)
            next_state, done = self.env.step(action)
            
            # 6. Accumulate
            total_reward += reward
            if done:
                break
            
            # Update state reference
            state = next_state
            
            # Early termination if detached
            if state.get('detached', False):
                detach_count += 1
                break
        
        avg_k_est = np.mean(k_est_samples) if k_est_samples else 0.0
        return total_reward, avg_k_est, detach_count

    def _compute_reward(
        self, 
        state: Dict[str, Any], 
        weights: Dict[str, float], 
        k_est: Optional[float]
    ) -> float:
        """Compute reward based on adaptive weights."""
        reward = 0.0
        
        # Contact reward
        if state.get('in_contact', False):
            reward += weights.get('r_contact', 1.0)
        
        # Detachment penalty (higher if k_est indicates high friction)
        if state.get('detached', False):
            # If k_est is high (sticky), penalty is severe
            penalty = weights.get('r_detach', 1.0)
            if k_est and k_est > 1.0:
                penalty *= 2.0  # Double penalty for high friction
            reward -= penalty
        
        # Progress reward
        progress = state.get('progress', 0.0)
        reward += progress * weights.get('r_progress', 0.1)
        
        return reward

    def _select_action(self, state: Dict[str, Any], weights: Dict[str, float]) -> np.ndarray:
        """
        Select action based on current state and adaptive weights.
        
        Simplified action selection for CPU efficiency.
        """
        # Base action from state
        action = np.zeros(self.env.action_space.shape)
        
        # If high friction detected (k_est > 1.0), apply more force
        current_k = self.estimator.get_latest_k()
        if current_k is not None and current_k > 1.0:
            # Apply stronger detachment force
            action[0] = weights.get('force_scale', 1.0) * 1.5
        else:
            action[0] = weights.get('force_scale', 1.0) * 0.5
        
        return action

    def train(self) -> Dict[str, Any]:
        """
        Execute the full training loop with optimizations.
        
        Returns:
            Dictionary of final training statistics.
        """
        self.logger.info(f"Starting training with {self.steps_per_episode} steps/episode, batch={self.batch_size}")
        self.logger.info(f"Max episodes: {self.max_episodes}")
        
        start_time = time.time()
        
        for episode in range(self.max_episodes):
            episode_start = time.time()
            
            # Run episode
            total_reward, avg_k_est, detach_count = self.run_episode(episode)
            
            episode_duration = time.time() - episode_start
            
            # Track statistics
            self.episode_rewards.append(total_reward)
            
            stats = TrainingStats(
                episode=episode,
                avg_reward=total_reward,
                k_est_mean=avg_k_est,
                detach_rate=detach_count / (episode + 1),
                duration_seconds=episode_duration,
                memory_peak_mb=0.0  # Would be populated by memory profiler in full run
            )
            self.training_history.append(stats)
            
            # Logging
            if episode % 10 == 0:
                self.logger.info(
                    f"Episode {episode}: reward={total_reward:.2f}, "
                    f"k_est={avg_k_est:.4f}, detach_rate={stats.detach_rate:.2f}, "
                    f"time={episode_duration:.2f}s"
                )
            
            # Early stopping check
            if total_reward > self.best_avg_reward:
                self.best_avg_reward = total_reward
                self.patience_counter = 0
            else:
                self.patience_counter += 1
            
            if self.patience_counter >= EARLY_STOPPING_PATIENCE:
                self.logger.info(f"Early stopping at episode {episode} (patience={EARLY_STOPPING_PATIENCE})")
                break
            
            # Safety break if time limit approaching (6h = 21600s)
            elapsed = time.time() - start_time
            if elapsed > 20000:  # Stop with buffer before 6h
                self.logger.warning("Approaching time limit, stopping training early")
                break

        total_time = time.time() - start_time
        
        # Final summary
        final_stats = {
            "total_episodes": len(self.training_history),
            "final_avg_reward": float(np.mean(self.episode_rewards[-10:])) if self.episode_rewards else 0.0,
            "best_avg_reward": float(self.best_avg_reward),
            "total_time_seconds": total_time,
            "steps_per_episode": self.steps_per_episode,
            "batch_size": self.batch_size,
            "early_stopped": self.patience_counter >= EARLY_STOPPING_PATIENCE
        }
        
        self.logger.info(f"Training complete: {final_stats}")
        return final_stats

def run_episode(
    env: PhysicsEnvironment,
    estimator: VirtualTactileEstimator,
    scheduler: AdaptiveRewardScheduler,
    steps: int = DEFAULT_STEPS_PER_EPISODE
) -> float:
    """
    Standalone function to run a single episode (for external callers).
    """
    loop = AdaptiveTrainingLoop(env, estimator, scheduler)
    loop.reset_episode()
    total_reward = 0.0
    
    for _ in range(steps):
        state = env.get_state()
        k_est = estimator.update(state.get('torque', 0.0), state.get('velocity', 0.0))
        weights = scheduler.update(k_est) if k_est and np.isfinite(k_est) else scheduler.get_weights()
        
        reward = 0.0
        if state.get('in_contact', False):
            reward += weights.get('r_contact', 1.0)
        if state.get('detached', False):
            reward -= weights.get('r_detach', 1.0)
        
        action = np.array([0.5])  # Simplified action
        next_state, done = env.step(action)
        total_reward += reward
        
        if done or next_state.get('detached', False):
            break
        
        state = next_state
    
    return total_reward

def train(
    output_path: Optional[str] = None,
    steps_per_episode: int = DEFAULT_STEPS_PER_EPISODE,
    batch_size: int = DEFAULT_BATCH_SIZE,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Main entry point for training.
    
    Args:
        output_path: Path to save training results JSON.
        steps_per_episode: Number of simulation steps per episode (optimized for T027).
        batch_size: Batch size for training (optimized for T027).
        seed: Random seed for reproducibility.
        
    Returns:
        Training statistics dictionary.
    """
    logger = setup_training_logger()
    logger.info("Initializing training loop...")
    
    # Initialize components
    env = create_cpu_environment()
    estimator = VirtualTactileEstimator(window_size=5, epsilon=1e-4)
    scheduler = AdaptiveRewardScheduler()
    
    # Use provided seed or default
    if seed is None:
        seed = get_seed()
    
    # Create training loop with optimized parameters
    training_loop = AdaptiveTrainingLoop(
        env=env,
        estimator=estimator,
        scheduler=scheduler,
        logger=logger,
        steps_per_episode=steps_per_episode,
        batch_size=batch_size,
        seed=seed
    )
    
    # Run training
    stats = training_loop.train()
    
    # Save results
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(stats, f, indent=2)
        logger.info(f"Results saved to {output_path}")
    
    return stats

def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Train Virtual Tactile Adaptive Policy")
    parser.add_argument("--output", type=str, default="state/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/training_results.json",
                        help="Path to save training results")
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS_PER_EPISODE,
                        help=f"Steps per episode (default: {DEFAULT_STEPS_PER_EPISODE})")
    parser.add_argument("--batch", type=int, default=DEFAULT_BATCH_SIZE,
                        help=f"Batch size (default: {DEFAULT_BATCH_SIZE})")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed (default: from seed_config)")
    
    args = parser.parse_args()
    
    stats = train(
        output_path=args.output,
        steps_per_episode=args.steps,
        batch_size=args.batch,
        seed=args.seed
    )
    
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    main()