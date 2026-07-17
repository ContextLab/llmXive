"""
Training loop for Virtual Tactile Zero-Shot Adaptation.

Integrates VirtualTactileEstimator and AdaptiveRewardScheduler to adapt
reward weights dynamically based on estimated stiffness coefficient (k_est).

Includes integration of estimator validation (T022) to log and verify
k_est stability and accuracy during training episodes.
"""

import os
import sys
import time
import json
import logging
import numpy as np
from typing import Dict, Any, List, Tuple, Optional

# Project imports
from environment import PhysicsEnvironment, create_cpu_environment
from estimator import VirtualTactileEstimator
from scheduler import AdaptiveRewardScheduler
from logging_config import setup_training_logger, init_logging
from seed_config import set_seeds, get_seed

# Validation imports (for T022 integration)
from validation import validate_estimator_during_episode, EstimatorValidationResult

def run_episode(
    env: PhysicsEnvironment,
    estimator: VirtualTactileEstimator,
    scheduler: AdaptiveRewardScheduler,
    episode_id: int,
    friction_coeff: float,
    max_steps: int = 200,
    logger: Optional[logging.Logger] = None,
    enable_validation: bool = True
) -> Dict[str, Any]:
    """
    Run a single training episode with adaptive reward scheduling.

    Args:
        env: The physics environment instance.
        estimator: The VirtualTactileEstimator instance.
        scheduler: The AdaptiveRewardScheduler instance.
        episode_id: Unique identifier for the episode.
        friction_coeff: The ground-truth friction coefficient for this object.
        max_steps: Maximum simulation steps per episode.
        logger: Optional logger for detailed tracking.
        enable_validation: If True, run estimator validation metrics (T022).

    Returns:
        Dictionary containing episode metrics and validation results.
    """
    logger = logger or logging.getLogger(__name__)

    # Reset environment
    obs = env.reset()
    estimator.reset()
    scheduler.reset()

    episode_log = {
        "episode_id": episode_id,
        "friction_coeff": friction_coeff,
        "steps": [],
        "k_est_history": [],
        "reward_weights_history": [],
        "validation": None
    }

    total_reward = 0.0
    success = False
    detach_time = None

    # T022: Initialize validation tracker if enabled
    validation_tracker = None
    if enable_validation:
        validation_tracker = []

    for step in range(max_steps):
        # 1. Estimate stiffness (k_est)
        torque = env.get_joint_torque()
        velocity = env.get_joint_velocity()
        
        k_est = estimator.update(torque, velocity)
        episode_log["k_est_history"].append(float(k_est))

        # 2. Adapt reward weights based on k_est
        current_weights = scheduler.update(k_est)
        episode_log["reward_weights_history"].append({
            "contact": float(current_weights["contact"]),
            "detach": float(current_weights["detach"])
        })

        # 3. Compute reward and step
        # (Simplified reward logic for demonstration; actual logic depends on env)
        reward = env.compute_reward(weights=current_weights)
        total_reward += reward

        # 4. Step environment
        obs, done, info = env.step(action=env.get_next_action())

        # 5. Log step data
        step_data = {
            "step": step,
            "reward": float(reward),
            "done": bool(done)
        }
        episode_log["steps"].append(step_data)

        # T022: Collect validation data for this step
        if enable_validation and validation_tracker is not None:
            validation_tracker.append({
                "step": step,
                "k_est": float(k_est),
                "ground_truth_friction": friction_coeff,
                "velocity": float(velocity),
                "torque": float(torque)
            })

        if done:
            if "detach" in info:
                detach_time = step
            success = info.get("success", False)
            break

    # T022: Finalize validation results
    validation_result = None
    if enable_validation and validation_tracker:
        # Run the validation logic defined in validation.py
        # This calculates error metrics (MAE, correlation) for the episode
        v_result = validate_estimator_during_episode(
            tracker=validation_tracker,
            ground_truth_friction=friction_coeff
        )
        validation_result = {
            "mae": float(v_result.mae),
            "correlation": float(v_result.correlation),
            "stability_variance": float(v_result.stability_variance),
            "total_steps_validated": len(validation_tracker)
        }
        episode_log["validation"] = validation_result

        # Log summary validation metrics
        logger.info(
            f"Episode {episode_id} Validation: "
            f"MAE={v_result.mae:.4f}, Corr={v_result.correlation:.4f}, "
            f"Var={v_result.stability_variance:.6f}"
        )

    episode_log["total_reward"] = float(total_reward)
    episode_log["success"] = success
    episode_log["detach_time"] = detach_time
    episode_log["final_k_est"] = float(estimator.get_current_estimate())

    return episode_log

def train(
    num_episodes: int = 50,
    friction_range: Tuple[float, float] = (0.1, 1.5),
    max_steps: int = 200,
    log_dir: str = "data/logs",
    enable_validation: bool = True
) -> Dict[str, Any]:
    """
    Main training loop.

    Args:
        num_episodes: Number of training episodes to run.
        friction_range: (min, max) friction coefficients to sample.
        max_steps: Steps per episode.
        log_dir: Directory to save training logs.
        enable_validation: If True, run estimator validation (T022) per episode.

    Returns:
        Aggregated training metrics.
    """
    # Setup logging
    os.makedirs(log_dir, exist_ok=True)
    logger = setup_training_logger(log_dir)
    logger.info(f"Starting training for {num_episodes} episodes.")
    logger.info(f"Friction range: {friction_range}")

    # Initialize components
    env = create_cpu_environment()
    estimator = VirtualTactileEstimator(window_size=5, epsilon=1e-4)
    scheduler = AdaptiveRewardScheduler()
    
    # Seed for reproducibility
    set_seeds(get_seed())

    all_logs = []
    start_time = time.time()

    for ep_id in range(num_episodes):
        # Sample friction for this episode
        friction = np.random.uniform(friction_range[0], friction_range[1])
        logger.info(f"Episode {ep_id}: Friction = {friction:.3f}")

        try:
            log = run_episode(
                env=env,
                estimator=estimator,
                scheduler=scheduler,
                episode_id=ep_id,
                friction_coeff=friction,
                max_steps=max_steps,
                logger=logger,
                enable_validation=enable_validation
            )
            all_logs.append(log)

            # Save individual episode log
            log_path = os.path.join(log_dir, f"episode_{ep_id:04d}.json")
            with open(log_path, "w") as f:
                json.dump(log, f, indent=2)

        except Exception as e:
            logger.error(f"Episode {ep_id} failed: {e}", exc_info=True)
            continue

    elapsed = time.time() - start_time
    logger.info(f"Training completed in {elapsed:.2f} seconds.")

    # Aggregate metrics
    total_success = sum(1 for l in all_logs if l["success"])
    success_rate = total_success / len(all_logs) if all_logs else 0.0

    avg_reward = np.mean([l["total_reward"] for l in all_logs]) if all_logs else 0.0

    # Aggregate validation metrics if available
    validation_stats = {}
    if enable_validation and any(l.get("validation") for l in all_logs):
        maes = [l["validation"]["mae"] for l in all_logs if l.get("validation")]
        corrs = [l["validation"]["correlation"] for l in all_logs if l.get("validation")]
        validation_stats = {
            "avg_mae": float(np.mean(maes)) if maes else 0.0,
            "avg_correlation": float(np.mean(corrs)) if corrs else 0.0
        }
        logger.info(f"Validation Stats: MAE={validation_stats['avg_mae']:.4f}, "
                    f"Corr={validation_stats['avg_correlation']:.4f}")

    summary = {
        "num_episodes": num_episodes,
        "completed_episodes": len(all_logs),
        "success_rate": success_rate,
        "avg_reward": avg_reward,
        "total_time_seconds": elapsed,
        "validation": validation_stats
    }

    summary_path = os.path.join(log_dir, "training_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    return summary

def main():
    """CLI entry point for training."""
    import argparse

    parser = argparse.ArgumentParser(description="Train Virtual Tactile Adaptation Policy")
    parser.add_argument("--episodes", type=int, default=50, help="Number of episodes")
    parser.add_argument("--friction-min", type=float, default=0.1)
    parser.add_argument("--friction-max", type=float, default=1.5)
    parser.add_argument("--log-dir", type=str, default="data/logs")
    parser.add_argument("--no-validation", action="store_true", help="Disable T022 validation")
    args = parser.parse_args()

    train(
        num_episodes=args.episodes,
        friction_range=(args.friction_min, args.friction_max),
        log_dir=args.log_dir,
        enable_validation=not args.no_validation
    )

if __name__ == "__main__":
    main()
