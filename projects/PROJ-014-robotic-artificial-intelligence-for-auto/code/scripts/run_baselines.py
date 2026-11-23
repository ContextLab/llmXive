import os
import sys
import json
import time
import random
import traceback
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import get_config, init_config, set_seed, get_path
from src.utils.logger import log_metrics, start_logging, stop_logging, get_logger
from src.environment.baselines import (
    create_pure_pursuit_controller,
    create_dijkstra_planner,
    create_stochastic_policy,
    PurePursuitConfig,
    DijkstraConfig,
    StochasticPolicy
)
from src.environment.sim_wrapper import create_sim_wrapper, NoiseConfig
from src.environment.checkpoint_manager import create_checkpoint_manager, CheckpointState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(get_path('results/baseline_execution.log')),
        logging.StreamHandler()
    ]
)
logger = get_logger('baselines')

def run_single_episode(
    seed: int,
    planner_type: str,
    config: Dict[str, Any],
    checkpoint_manager: Any = None
) -> Dict[str, Any]:
    """
    Run a single episode with the specified planner.
    Returns a dictionary with success status, path optimality, and other metrics.
    """
    set_seed(seed)
    result = {
        "seed": seed,
        "planner_type": planner_type,
        "success": False,
        "path_optimality": None,
        "steps": 0,
        "crashed": False,
        "error": None
    }

    try:
        # Initialize simulation environment
        sim_wrapper = create_sim_wrapper(
            noise_config=NoiseConfig(
                sensor_noise=0.0,
                action_noise=0.0
            )
        )
        
        # Initialize planner based on type
        if planner_type == "pure_pursuit":
            planner = create_pure_pursuit_controller(
                PurePursuitConfig(
                    lookahead_distance=config.get("lookahead_distance", 2.0),
                    speed=config.get("speed", 1.0)
                )
            )
        elif planner_type == "dijkstra":
            planner = create_dijkstra_planner(
                DijkstraConfig(
                    resolution=config.get("resolution", 0.5),
                    max_iterations=config.get("max_iterations", 1000)
                )
            )
        elif planner_type == "stochastic":
            planner = create_stochastic_policy()
        else:
            raise ValueError(f"Unknown planner type: {planner_type}")

        # Reset environment
        state = sim_wrapper.reset()
        done = False
        steps = 0
        max_steps = config.get("max_steps", 1000)
        
        total_reward = 0.0
        optimal_path_length = config.get("optimal_path_length", 100.0)
        actual_path_length = 0.0

        while not done and steps < max_steps:
            # Get action from planner
            action = planner.get_action(state)
            
            # Step environment
            next_state, reward, done, info = sim_wrapper.step(action)
            
            # Track path length (assuming reward relates to progress or distance)
            # In a real simulation, this would be computed from actual trajectory
            actual_path_length += abs(reward) if reward < 0 else 0 
            # Simplified: assuming negative reward is distance traveled
            
            total_reward += reward
            steps += 1
            state = next_state

            # Check for crash/failure
            if info.get("crashed") or info.get("failure"):
                result["crashed"] = True
                done = True
                break

        # Calculate metrics
        if not result["crashed"] and done:
            result["success"] = True
            # Path optimality: ratio of optimal to actual path length
            # Lower is better, but we report as a ratio where 1.0 is perfect
            if actual_path_length > 0:
                result["path_optimality"] = optimal_path_length / actual_path_length
            else:
                result["path_optimality"] = 1.0
        else:
            result["success"] = False
            result["path_optimality"] = 0.0

        result["steps"] = steps

    except Exception as e:
        logger.error(f"Episode {seed} failed with error: {str(e)}")
        result["crashed"] = True
        result["error"] = str(e)
        result["success"] = False
        result["path_optimality"] = 0.0

    return result

def save_results(results: List[Dict[str, Any]], output_path: str):
    """
    Save baseline results to a JSON file.
    Includes aggregated metrics: success_rate, path_optimality (mean), seeds.
    """
    if not results:
        logger.warning("No results to save.")
        return

    # Aggregate metrics
    successful_runs = [r for r in results if r["success"]]
    success_rate = len(successful_runs) / len(results) if results else 0.0
    
    optimality_values = [r["path_optimality"] for r in successful_runs if r["path_optimality"] is not None]
    mean_optimality = sum(optimality_values) / len(optimality_values) if optimality_values else 0.0

    summary = {
        "success_rate": success_rate,
        "path_optimality": mean_optimality,
        "seeds": [r["seed"] for r in results],
        "planner_type": results[0]["planner_type"] if results else None,
        "total_episodes": len(results),
        "successful_episodes": len(successful_runs),
        "failed_episodes": len(results) - len(successful_runs),
        "individual_results": results
    }

    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path_obj, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    logger.info(f"Success Rate: {success_rate:.4f}, Mean Path Optimality: {mean_optimality:.4f}")

def load_results(input_path: str) -> List[Dict[str, Any]]:
    """
    Load existing results from a JSON file.
    """
    path = Path(input_path)
    if not path.exists():
        return []
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    return data.get("individual_results", [])

def run_baselines(
    planner_type: str,
    num_seeds: int = 30,
    checkpoint_path: str = None,
    config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Run baselines for N seeds.
    Handles crashes via checkpointing if enabled.
    """
    if config is None:
        config = {
            "lookahead_distance": 2.0,
            "speed": 1.0,
            "resolution": 0.5,
            "max_iterations": 1000,
            "max_steps": 1000,
            "optimal_path_length": 100.0
        }

    results = []
    checkpoint_manager = None
    start_seed = 0

    # Checkpointing logic
    if checkpoint_path:
        checkpoint_manager = create_checkpoint_manager(checkpoint_path)
        existing_state = checkpoint_manager.load()
        if existing_state:
            results = existing_state.get("results", [])
            start_seed = existing_state.get("next_seed", 0)
            logger.info(f"Resuming from seed {start_seed}")

    for seed in range(start_seed, num_seeds):
        try:
            logger.info(f"Running seed {seed} for {planner_type}")
            episode_result = run_single_episode(seed, planner_type, config, checkpoint_manager)
            results.append(episode_result)

            # Save checkpoint after each episode if enabled
            if checkpoint_manager:
                checkpoint_manager.save(CheckpointState(
                    results=results,
                    next_seed=seed + 1
                ))

        except Exception as e:
            logger.error(f"Critical error at seed {seed}: {e}")
            # If checkpointing is off, we might want to break or continue
            if not checkpoint_manager:
                raise
            else:
                # Log error and continue to next seed
                continue

    return results

def main():
    """
    Main entry point for running baselines.
    """
    # Initialize config
    init_config()
    
    # Parse arguments (simplified for this script)
    planner_type = os.getenv("BASELINE_PLANNER", "pure_pursuit")
    num_seeds = int(os.getenv("BASELINE_SEEDS", "30"))
    output_path = get_path('results/baseline_metrics.json')
    checkpoint_path = get_path('results/baseline_checkpoint.pkl')

    logger.info(f"Starting baseline execution: {planner_type}, {num_seeds} seeds")

    # Start resource logging
    start_logging(interval=1)

    try:
        results = run_baselines(
            planner_type=planner_type,
            num_seeds=num_seeds,
            checkpoint_path=checkpoint_path
        )
        
        save_results(results, output_path)

    finally:
        stop_logging()
        logger.info("Baseline execution finished.")

if __name__ == "__main__":
    main()