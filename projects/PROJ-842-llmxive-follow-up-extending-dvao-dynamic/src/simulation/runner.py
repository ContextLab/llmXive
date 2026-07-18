"""
Runner module for DVAO simulation experiments.

Executes CPU-constrained training loops with memory checks (<7GB)
and supports multi-objective MDP generation with configurable noise correlation.
"""
import argparse
import json
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, Any, Optional

# Import from project modules
from ..simulation.synthetic_mdp import generate_multi_objective_mdp
from ..simulation.heuristic import MovingWindowHeuristic
from ..config.defaults import load_config

def check_memory_usage(max_gb: float = 7.0) -> bool:
    """
    Check current memory usage.
    
    Args:
        max_gb: Maximum allowed memory in GB.
        
    Returns:
        True if memory usage is within limits, False otherwise.
    """
    try:
        import resource
        # Get memory usage in KB (RUSAGE_SELF for current process)
        mem_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        mem_gb = mem_kb / (1024 * 1024)  # Convert KB to GB
        
        if mem_gb > max_gb:
            print(f"WARNING: Memory usage ({mem_gb:.2f} GB) exceeds limit ({max_gb} GB)")
            return False
        return True
    except Exception as e:
        print(f"Could not check memory usage: {e}")
        return True  # Allow execution if check fails

def run_simulation(
    n_objectives: int,
    seed: int,
    noise_correlation: float,
    window_size: int = 10,
    num_episodes: int = 100,
    max_steps_per_episode: int = 200,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run a single simulation experiment.
    
    Args:
        n_objectives: Number of objectives (N).
        seed: Random seed for reproducibility.
        noise_correlation: Noise correlation parameter ρ ∈ {0, 0.2, 0.5}.
        window_size: Size of the moving window for heuristic (k).
        num_episodes: Number of episodes to run.
        max_steps_per_episode: Maximum steps per episode.
        output_dir: Directory to write results (default: data/processed).
        
    Returns:
        Dictionary containing simulation results.
    """
    # Validate inputs
    if n_objectives <= 0:
        raise ValueError(f"n_objectives must be positive, got {n_objectives}")
    if noise_correlation not in [0.0, 0.2, 0.5]:
        raise ValueError(f"noise_correlation must be one of [0.0, 0.2, 0.5], got {noise_correlation}")
    if seed < 0:
        raise ValueError(f"seed must be non-negative, got {seed}")
        
    # Set output directory
    if output_dir is None:
        output_dir = "data/processed"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Starting simulation: N={n_objectives}, ρ={noise_correlation}, seed={seed}")
    print(f"Memory limit: 7.0 GB")
    
    # Initialize MDP
    print("Generating multi-objective MDP...")
    mdp = generate_multi_objective_mdp(
        n_objectives=n_objectives,
        seed=seed,
        noise_correlation=noise_correlation
    )
    
    # Initialize heuristic
    print(f"Initializing Moving-Window Heuristic with k={window_size}...")
    heuristic = MovingWindowHeuristic(window_size=window_size)
    
    # Results storage
    results = {
        "n_objectives": n_objectives,
        "noise_correlation": noise_correlation,
        "seed": seed,
        "window_size": window_size,
        "num_episodes": num_episodes,
        "max_steps_per_episode": max_steps_per_episode,
        "episodes": [],
        "summary": {}
    }
    
    total_steps = 0
    start_time = time.time()
    
    # Run episodes
    for ep_idx in range(num_episodes):
        # Check memory periodically
        if ep_idx % 10 == 0 and ep_idx > 0:
            if not check_memory_usage(max_gb=7.0):
                print(f"Memory limit exceeded at episode {ep_idx}. Stopping.")
                break
            
        episode_data = {
            "episode": ep_idx,
            "steps": [],
            "total_reward": 0.0,
            "variance_estimates": []
        }
        
        # Reset environment
        state = mdp.reset(seed=seed + ep_idx)
        step_reward = 0.0
        
        for step in range(max_steps_per_episode):
            # Check memory
            if step % 50 == 0 and step > 0:
                if not check_memory_usage(max_gb=7.0):
                    print(f"Memory limit exceeded at step {step} of episode {ep_idx}. Stopping.")
                    break
            
            # Select action (random for now, can be replaced with policy)
            action = mdp.action_space.sample()
            
            # Step environment
            next_state, reward, terminated, truncated, info = mdp.step(action)
            
            # Update heuristic with reward
            variance_estimate = heuristic.update(reward)
            
            # Record step data
            episode_data["steps"].append({
                "step": step,
                "state": state,
                "action": action,
                "reward": reward,
                "next_state": next_state,
                "terminated": terminated,
                "truncated": truncated,
                "variance_estimate": variance_estimate
            })
            
            episode_data["total_reward"] += reward
            episode_data["variance_estimates"].append(variance_estimate)
            
            state = next_state
            total_steps += 1
            
            if terminated or truncated:
                break
        
        results["episodes"].append(episode_data)
        
        # Print progress
        if (ep_idx + 1) % 20 == 0:
            elapsed = time.time() - start_time
            print(f"Completed {ep_idx + 1}/{num_episodes} episodes ({elapsed:.2f}s)")
    
    # Calculate summary statistics
    total_rewards = [ep["total_reward"] for ep in results["episodes"]]
    all_variances = []
    for ep in results["episodes"]:
        all_variances.extend(ep["variance_estimates"])
    
    results["summary"] = {
        "total_episodes": len(results["episodes"]),
        "total_steps": total_steps,
        "mean_total_reward": sum(total_rewards) / len(total_rewards) if total_rewards else 0.0,
        "std_total_reward": (sum((r - results["summary"]["mean_total_reward"]) ** 2 for r in total_rewards) / len(total_rewards)) ** 0.5 if total_rewards else 0.0,
        "mean_variance_estimate": sum(all_variances) / len(all_variances) if all_variances else 0.0,
        "std_variance_estimate": (sum((v - results["summary"]["mean_variance_estimate"]) ** 2 for v in all_variances) / len(all_variances)) ** 0.5 if all_variances else 0.0,
        "elapsed_time_seconds": time.time() - start_time
    }
    
    # Write results to file
    output_file = Path(output_dir) / f"simulation_N{n_objectives}_rho{noise_correlation}_seed{seed}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results written to {output_file}")
    print(f"Simulation completed successfully. Total steps: {total_steps}, Mean reward: {results['summary']['mean_total_reward']:.4f}")
    
    return results

def main():
    """Main entry point for the simulation runner."""
    parser = argparse.ArgumentParser(
        description="Run DVAO simulation experiments with multi-objective MDPs."
    )
    parser.add_argument(
        "--n-objectives",
        type=int,
        default=10,
        help="Number of objectives (N). Default: 10"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility. Default: 42"
    )
    parser.add_argument(
        "--noise-correlation",
        type=float,
        choices=[0.0, 0.2, 0.5],
        default=0.0,
        help="Noise correlation parameter ρ. Choices: [0.0, 0.2, 0.5]. Default: 0.0"
    )
    parser.add_argument(
        "--window-size",
        type=int,
        default=10,
        help="Moving window size k for heuristic. Default: 10"
    )
    parser.add_argument(
        "--num-episodes",
        type=int,
        default=100,
        help="Number of episodes to run. Default: 100"
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=200,
        help="Maximum steps per episode. Default: 200"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Directory to write output files. Default: data/processed"
    )
    
    args = parser.parse_args()
    
    try:
        print(f"Running simulation with parameters:")
        print(f"  N (objectives): {args.n_objectives}")
        print(f"  Seed: {args.seed}")
        print(f"  ρ (noise correlation): {args.noise_correlation}")
        print(f"  Window size (k): {args.window_size}")
        print(f"  Episodes: {args.num_episodes}")
        print(f"  Max steps: {args.max_steps}")
        print(f"  Output dir: {args.output_dir}")
        
        results = run_simulation(
            n_objectives=args.n_objectives,
            seed=args.seed,
            noise_correlation=args.noise_correlation,
            window_size=args.window_size,
            num_episodes=args.num_episodes,
            max_steps_per_episode=args.max_steps,
            output_dir=args.output_dir
        )
        
        # Final memory check
        if not check_memory_usage(max_gb=7.0):
            print("WARNING: Final memory check failed.")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"ERROR: Simulation failed with exception: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
