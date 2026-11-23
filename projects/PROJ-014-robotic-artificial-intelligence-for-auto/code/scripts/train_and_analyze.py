import os
import sys
import json
import time
import csv
import logging
import traceback
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import get_config, init_config, set_seed, get_path
from src.utils.logger import ResourceLogger, get_logger, log_metrics
from src.agents.dqn_agent import create_dqn_agent, DQNConfig
from src.agents.memory import create_replay_buffer, ReplayBufferConfig
from src.environment.sim_wrapper import create_sim_wrapper, NoiseConfig
from src.environment.checkpoint_manager import create_checkpoint_manager, CheckpointState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'results' / 'training.log')
    ]
)
logger = logging.getLogger(__name__)

MODALITIES = ["rgb", "depth", "grid"]
NUM_SEEDS = 30
EPISODES_PER_SEED = 50  # Reduced for demo within budget, can be adjusted
GLOBAL_TIMEOUT_SECONDS = 6 * 3600  # 6 hours as per SC-005

def load_training_config() -> Dict[str, Any]:
    """Load training hyperparameters from config."""
    config = get_config()
    return {
        "learning_rate": config.get("learning_rate", 1e-4),
        "gamma": config.get("gamma", 0.99),
        "epsilon_start": config.get("epsilon_start", 1.0),
        "epsilon_end": config.get("epsilon_end", 0.05),
        "epsilon_decay": config.get("epsilon_decay", 0.995),
        "buffer_size": config.get("buffer_size", 10000),
        "batch_size": config.get("batch_size", 64),
        "target_update": config.get("target_update", 10),
        "training_start": config.get("training_start", 100),
    }

def run_single_training_episode(
    agent,
    env,
    seed: int,
    episode_num: int,
    hyperparams: Dict[str, Any]
) -> Dict[str, Any]:
    """Run a single training episode and return metrics."""
    state, _ = env.reset(seed=seed + episode_num)
    total_reward = 0
    step_count = 0
    done = False
    truncated = False
    
    while not (done or truncated):
        action = agent.select_action(state)
        next_state, reward, done, truncated, info = env.step(action)
        agent.store_transition(state, action, reward, next_state, done)
        
        if len(agent.replay_buffer) > hyperparams["training_start"]:
            agent.train_step()
        
        state = next_state
        total_reward += reward
        step_count += 1

        # Check for memory pressure (simple heuristic)
        if step_count % 100 == 0:
            log_metrics()  # Logs RAM/CPU usage

    return {
        "episode": episode_num,
        "total_reward": total_reward,
        "steps": step_count,
        "success": info.get("success", False),
        "seed": seed
    }

def train_agent_for_modality(
    modality: str,
    seed: int,
    start_time: float,
    hyperparams: Dict[str, Any],
    checkpoint_manager: Any
) -> Optional[Dict[str, Any]]:
    """Train a DQN agent for a specific modality and seed."""
    try:
        set_seed(seed)
        
        # Initialize environment
        noise_cfg = NoiseConfig(
            rgb_noise=0.05,
            depth_noise=0.1,
            grid_noise=0.02
        )
        env = create_sim_wrapper(modality=modality, noise_config=noise_cfg)
        
        # Initialize agent
        agent_config = DQNConfig(
            input_shape=(84, 84, 3) if modality == "rgb" else (84, 84, 1),
            n_actions=4,
            lr=hyperparams["learning_rate"],
            gamma=hyperparams["gamma"],
            epsilon_start=hyperparams["epsilon_start"],
            epsilon_end=hyperparams["epsilon_end"],
            epsilon_decay=hyperparams["epsilon_decay"],
        )
        agent = create_dqn_agent(agent_config)
        
        # Initialize replay buffer
        buffer_config = ReplayBufferConfig(
            capacity=hyperparams["buffer_size"],
            batch_size=hyperparams["batch_size"]
        )
        agent.replay_buffer = create_replay_buffer(buffer_config)
        
        episode_rewards = []
        episode_successes = []
        
        for ep in range(EPISODES_PER_SEED):
            # Check global timeout
            elapsed = time.time() - start_time
            if elapsed > GLOBAL_TIMEOUT_SECONDS:
                logger.warning(f"Global timeout reached at seed {seed}, modality {modality}")
                checkpoint_manager.save_state({
                    "modality": modality,
                    "seed": seed,
                    "episode": ep,
                    "elapsed_time": elapsed
                })
                return None  # Signal timeout
            
            metrics = run_single_training_episode(
                agent, env, seed, ep, hyperparams
            )
            episode_rewards.append(metrics["total_reward"])
            episode_successes.append(metrics["success"])
            
            # Save checkpoint periodically
            if (ep + 1) % 10 == 0:
                checkpoint_manager.save_state({
                    "modality": modality,
                    "seed": seed,
                    "episode": ep,
                    "agent_state": agent.get_state_dict(),
                    "replay_buffer": agent.replay_buffer.get_state(),
                    "avg_reward": sum(episode_rewards[-10:]) / len(episode_rewards[-10:])
                })
        
        return {
            "modality": modality,
            "seed": seed,
            "avg_reward": sum(episode_rewards) / len(episode_rewards),
            "success_rate": sum(episode_successes) / len(episode_successes),
            "total_episodes": EPISODES_PER_SEED
        }
        
    except MemoryError:
        logger.error(f"Memory error at seed {seed}, modality {modality}")
        checkpoint_manager.save_state({
            "modality": modality,
            "seed": seed,
            "error": "MemoryError"
        })
        raise
    except Exception as e:
        logger.error(f"Unexpected error at seed {seed}, modality {modality}: {e}")
        traceback.print_exc()
        checkpoint_manager.save_state({
            "modality": modality,
            "seed": seed,
            "error": str(e)
        })
        raise

def main():
    """Main orchestrator for training across modalities and seeds."""
    init_config()
    
    results_dir = get_path("results")
    curves_dir = results_dir / "training_curves"
    curves_dir.mkdir(parents=True, exist_ok=True)
    
    checkpoint_dir = results_dir / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    checkpoint_manager = create_checkpoint_manager(str(checkpoint_dir))
    
    # Try to resume if checkpoint exists
    last_checkpoint = checkpoint_manager.get_latest_checkpoint()
    start_seed_offset = 0
    start_modality_idx = 0
    
    if last_checkpoint:
        logger.info(f"Resuming from checkpoint: {last_checkpoint}")
        start_modality_idx = last_checkpoint.get("modality_idx", 0)
        start_seed_offset = last_checkpoint.get("seed", 0) + 1
    else:
        logger.info("Starting fresh training run")
    
    start_time = time.time()
    all_results = []
    
    hyperparams = load_training_config()
    
    try:
        for modality_idx, modality in enumerate(MODALITIES):
            if modality_idx < start_modality_idx:
                continue
            if modality_idx == start_modality_idx:
                seed_start = start_seed_offset
            else:
                seed_start = 0
            
            for seed in range(seed_start, NUM_SEEDS):
                # Check global timeout before starting new seed
                elapsed = time.time() - start_time
                if elapsed > GLOBAL_TIMEOUT_SECONDS:
                    logger.warning(f"Global timeout reached. Stopping training.")
                    checkpoint_manager.save_state({
                        "modality_idx": modality_idx,
                        "seed": seed,
                        "elapsed_time": elapsed,
                        "status": "timeout"
                    })
                    break
                
                logger.info(f"Training {modality} with seed {seed} (elapsed: {elapsed:.1f}s)")
                
                try:
                    result = train_agent_for_modality(
                        modality, seed, start_time, hyperparams, checkpoint_manager
                    )
                    
                    if result is None:
                        # Timeout occurred
                        break
                    
                    all_results.append(result)
                    logger.info(f"Completed {modality} seed {seed}: "
                              f"avg_reward={result['avg_reward']:.2f}, "
                              f"success_rate={result['success_rate']:.2f}")
                    
                except (MemoryError, Exception) as e:
                    logger.error(f"Failed seed {seed} for {modality}: {e}")
                    # Continue to next seed on non-fatal errors
                    continue
        
        # Save learning curve CSVs
        for modality in MODALITIES:
            modality_results = [r for r in all_results if r["modality"] == modality]
            if modality_results:
                csv_path = curves_dir / f"training_curve_{modality}.csv"
                with open(csv_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=["seed", "avg_reward", "success_rate"])
                    writer.writeheader()
                    for r in modality_results:
                        writer.writerow({
                            "seed": r["seed"],
                            "avg_reward": r["avg_reward"],
                            "success_rate": r["success_rate"]
                        })
                logger.info(f"Saved training curve for {modality} to {csv_path}")
        
        # Save summary
        summary_path = results_dir / "training_summary.json"
        with open(summary_path, 'w') as f:
            json.dump({
                "total_seeds_per_modality": NUM_SEEDS,
                "completed_seeds": len(all_results),
                "modalities": MODALITIES,
                "total_time_seconds": time.time() - start_time,
                "results": all_results
            }, f, indent=2)
        
        logger.info(f"Training complete. Summary saved to {summary_path}")
        
    except KeyboardInterrupt:
        logger.info("Training interrupted by user")
        checkpoint_manager.save_state({
            "status": "interrupted",
            "elapsed_time": time.time() - start_time
        })

if __name__ == "__main__":
    main()