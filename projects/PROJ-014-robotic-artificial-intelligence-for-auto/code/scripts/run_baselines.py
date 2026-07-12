import os
import sys
import json
import time
import random
import traceback
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.utils.config import get_config, get_path, set_seed
from src.utils.logger import log_metrics, start_logging, stop_logging, get_resource_summary
from src.environment.baselines import (
    create_pure_pursuit_controller,
    create_dijkstra_planner,
    create_stochastic_policy,
    PurePursuitConfig,
    DijkstraConfig
)
from src.environment.sim_wrapper import create_sim_wrapper, NoiseConfig
from src.environment.checkpoint_manager import create_checkpoint_manager

def run_single_episode(
    seed: int,
    planner_type: str,
    config: Dict[str, Any],
    sim_wrapper,
    checkpoint_manager
) -> Dict[str, Any]:
    """
    Run a single episode for a specific planner type.
    Returns a dictionary with success status, path optimality, and steps.
    """
    set_seed(seed)
    
    # Initialize controller/planner based on type
    if planner_type == "pure_pursuit":
        controller = create_pure_pursuit_controller(PurePursuitConfig(
            lookhead_distance=config.get("lookhead_distance", 2.0),
            speed=config.get("speed", 1.0)
        ))
    elif planner_type == "dijkstra":
        controller = create_dijkstra_planner(DijkstraConfig(
            resolution=config.get("resolution", 0.5)
        ))
    elif planner_type == "stochastic":
        controller = create_stochastic_policy()
    else:
        raise ValueError(f"Unknown planner type: {planner_type}")

    state = sim_wrapper.reset(seed=seed)
    done = False
    total_reward = 0.0
    steps = 0
    success = False
    path_optimality = 1.0  # Default for stochastic/random

    # Load checkpoint if exists
    checkpoint_data = checkpoint_manager.load(seed, planner_type)
    if checkpoint_data:
        state = checkpoint_data["state"]
        steps = checkpoint_data["steps"]
        total_reward = checkpoint_data["total_reward"]
        # Resume simulation (simplified)

    try:
        while not done:
            action = controller.step(state)
            next_state, reward, done, info = sim_wrapper.step(action)
            
            total_reward += reward
            steps += 1
            state = next_state

            # Check for success/failure conditions (simulated)
            if info.get("success"):
                success = True
                # Calculate optimality: ratio of optimal path length to actual path length
                # In a real sim, we'd compare to ground truth path
                if planner_type != "stochastic":
                    optimal_path_len = info.get("optimal_path_length", 100)
                    actual_path_len = steps * 0.1 # Approximate step size
                    path_optimality = min(1.0, optimal_path_len / max(actual_path_len, 0.01))
                done = True
            elif info.get("failure") or info.get("timeout"):
                success = False
                path_optimality = 0.0
                done = True

            # Periodic checkpoint
            if steps % 10 == 0:
                checkpoint_manager.save({
                    "state": state,
                    "steps": steps,
                    "total_reward": total_reward,
                    "planner": planner_type,
                    "seed": seed
                }, seed, planner_type)

    except Exception as e:
        print(f"Episode {seed} crashed: {e}")
        traceback.print_exc()
        success = False
        path_optimality = 0.0

    finally:
        # Cleanup checkpoint on success or final failure
        if success or steps > 100:
            checkpoint_manager.cleanup(seed, planner_type)

    return {
        "seed": seed,
        "planner": planner_type,
        "success": success,
        "path_optimality": path_optimality,
        "steps": steps,
        "total_reward": total_reward
    }

def run_baselines(num_seeds: int = 30):
    """
    Orchestrate running baselines across multiple seeds.
    Logs results including success rates and path optimality ratios.
    """
    config = get_config()
    results_dir = get_path("results")
    Path(results_dir).mkdir(parents=True, exist_ok=True)
    
    output_file = Path(results_dir) / "baseline_metrics.json"
    
    # Initialize logging for resources
    start_logging(interval=1.0)
    
    # Initialize simulation and checkpoint manager
    sim_wrapper = create_sim_wrapper(NoiseConfig())
    checkpoint_manager = create_checkpoint_manager(str(Path(results_dir) / "checkpoints"))
    
    all_results = {
        "pure_pursuit": {"successes": 0, "optimality_sum": 0.0, "seeds": []},
        "dijkstra": {"successes": 0, "optimality_sum": 0.0, "seeds": []},
        "stochastic": {"successes": 0, "optimality_sum": 0.0, "seeds": []}
    }

    planners = ["pure_pursuit", "dijkstra", "stochastic"]
    
    try:
        for planner in planners:
            print(f"Running {planner} for {num_seeds} seeds...")
            for seed in range(num_seeds):
                print(f"  Seed {seed}...", end=" ", flush=True)
                try:
                    result = run_single_episode(
                        seed=seed,
                        planner_type=planner,
                        config=config.get("baselines", {}),
                        sim_wrapper=sim_wrapper,
                        checkpoint_manager=checkpoint_manager
                    )
                    
                    all_results[planner]["seeds"].append(result)
                    if result["success"]:
                        all_results[planner]["successes"] += 1
                        all_results[planner]["optimality_sum"] += result["path_optimality"]
                    
                    # Log metrics for this episode
                    log_metrics({
                        "episode_seed": seed,
                        "planner": planner,
                        "success": result["success"],
                        "path_optimality": result["path_optimality"],
                        "steps": result["steps"],
                        "cpu_percent": get_resource_summary()["cpu_percent"]
                    })
                    
                    print(f"Done (Success: {result['success']}, Opt: {result['path_optimality']:.2f})")
                except Exception as e:
                    print(f"Failed: {e}")
                    # Log failure
                    log_metrics({
                        "episode_seed": seed,
                        "planner": planner,
                        "success": False,
                        "path_optimality": 0.0,
                        "steps": 0,
                        "error": str(e)
                    })

        # Aggregate and save results
        final_report = {}
        for planner, data in all_results.items():
            count = len(data["seeds"])
            if count == 0:
                continue
            success_rate = data["successes"] / count
            avg_optimality = data["optimality_sum"] / data["successes"] if data["successes"] > 0 else 0.0
            
            final_report[planner] = {
                "success_rate": success_rate,
                "path_optimality": avg_optimality,
                "seeds": [s["seed"] for s in data["seeds"]]
            }
            
            # Log summary metrics
            log_metrics({
                "summary_planner": planner,
                "summary_success_rate": success_rate,
                "summary_avg_optimality": avg_optimality
            })

        # Write final report
        with open(output_file, 'w') as f:
            json.dump(final_report, f, indent=2)
        
        print(f"\nResults saved to {output_file}")
        return final_report

    finally:
        stop_logging()
        # Cleanup checkpoints
        checkpoint_manager.cleanup_all()

def main():
    """Entry point for running baselines."""
    num_seeds = int(os.getenv("NUM_SEEDS", 30))
    run_baselines(num_seeds=num_seeds)

if __name__ == "__main__":
    main()