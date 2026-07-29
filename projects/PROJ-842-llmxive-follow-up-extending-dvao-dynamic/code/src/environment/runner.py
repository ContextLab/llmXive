import argparse
import json
import os
import sys
import time
import traceback
import gc
import psutil
import tracemalloc

# Import from local modules
from src.environment.synthetic_mdp import SyntheticTabularMDP
from src.simulation.heuristic import MovingWindowVarianceHeuristic, calculate_windowed_variance
from src.analysis.pareto import distance_to_frontier
from src.analysis.stats import check_memory_limit, get_memory_usage_bytes, run_one_sample_ttest, run_stability_check

MEMORY_LIMIT_GB = 7.0

def enforce_cpu_cores(cores: int = 2) -> None:
    """
    Enforces CPU core usage by setting affinity and environment variables.
    
    Args:
        cores: Number of cores to pin the process to.
    """
    # Set OMP_NUM_THREADS
    os.environ['OMP_NUM_THREADS'] = str(cores)
    
    try:
        # Get all available CPUs
        all_cpus = list(range(psutil.cpu_count(logical=False)))
        if len(all_cpus) < cores:
            raise ValueError(f"System does not have enough physical cores. Available: {len(all_cpus)}, Requested: {cores}")
        
        # Pin to first `cores` physical CPUs
        selected_cpus = all_cpus[:cores]
        os.sched_setaffinity(0, selected_cpus)
        
        print(f"CPU Affinity set to cores: {selected_cpus}")
    except NotImplementedError:
        # os.sched_setaffinity not available on this platform (e.g., Windows)
        print(f"Warning: os.sched_setaffinity not available. Setting OMP_NUM_THREADS={cores} only.")
    except Exception as e:
        print(f"Warning: Could not set CPU affinity: {e}")

def check_memory_limit_and_exit(limit_gb: float = MEMORY_LIMIT_GB) -> None:
    """
    Checks memory usage and exits with code 1 if limit is exceeded.
    This is the runtime verification step for T056.
    """
    try:
        check_memory_limit(limit_gb)
    except MemoryError as e:
        print(f"FATAL: {e}", file=sys.stderr)
        sys.exit(1)

def generate_trajectories(mdp: SyntheticTabularMDP, n_episodes: int = 100, max_steps: int = 500) -> list:
    """
    Generates trajectories from the MDP.
    Returns a list of trajectories (state, action, reward tuples).
    """
    trajectories = []
    for _ in range(n_episodes):
        state = mdp.reset()
        episode = []
        for _ in range(max_steps):
            action = mdp.get_random_action()
            next_state, rewards, done, info = mdp.step(action)
            episode.append((state, action, rewards))
            state = next_state
            if done:
                break
        trajectories.append(episode)
    return trajectories

def run_simulation(args):
    """
    Main simulation loop.
    """
    # Enforce CPU constraints first
    enforce_cpu_cores(cores=2)
    
    # Start memory tracing
    tracemalloc.start()
    
    print(f"Starting simulation with N={args.n_objectives}, Seed={args.seed}")
    
    # Initialize MDP
    mdp = SyntheticTabularMDP(n_objectives=args.n_objectives, seed=args.seed)
    
    # Check memory after MDP creation
    check_memory_limit_and_exit(MEMORY_LIMIT_GB)
    
    # Initialize Heuristic
    heuristic = MovingWindowVarianceHeuristic(window_size=args.window_size)
    
    # Run episodes
    n_episodes = args.n_episodes
    all_variance_estimates = []
    all_pareto_distances = []
    
    for i in range(n_episodes):
        # Periodic memory check
        if i % 10 == 0:
            check_memory_limit_and_exit(MEMORY_LIMIT_GB)
        
        state = mdp.reset()
        episode_rewards = []
        
        for step in range(args.max_steps):
            action = mdp.get_random_action()
            next_state, rewards, done, info = mdp.step(action)
            episode_rewards.append(rewards)
            state = next_state
            
            if done:
                break
        
        # Calculate heuristic variance
        rewards_array = np.array(episode_rewards)
        var_est = calculate_windowed_variance(rewards_array, args.window_size)
        all_variance_estimates.append(var_est)
        
        # Calculate Pareto distance (placeholder for actual logic)
        # In a real scenario, this would use the policy's cumulative rewards
        dist = distance_to_frontier(np.mean(episode_rewards, axis=0))
        all_pareto_distances.append(dist)
        
        # Force garbage collection periodically
        if i % 50 == 0:
            gc.collect()
            
        # Final check
        if i == n_episodes - 1:
            check_memory_limit_and_exit(MEMORY_LIMIT_GB)
    
    # Stop tracing
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    print(f"Simulation completed. Peak memory: {peak / 1024**2:.2f} MB")
    
    # Save results
    results = {
        "n_objectives": args.n_objectives,
        "seed": args.seed,
        "empirical_variance": float(np.mean(all_variance_estimates)),
        "pareto_distance": float(np.mean(all_pareto_distances)),
        "peak_memory_mb": float(peak / 1024**2),
        "timestamp": time.time()
    }
    
    os.makedirs("data/processed", exist_ok=True)
    output_path = "data/processed/empirical_results.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    print(f"Results saved to {output_path}")
    return results

def main():
    parser = argparse.ArgumentParser(description="Runner for DVAO experiments")
    parser.add_argument("--n-objectives", type=int, default=50, help="Number of objectives N")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--noise-correlation", type=float, default=0.0, help="Noise correlation parameter rho")
    parser.add_argument("--window-size", type=int, default=10, help="Window size k for heuristic")
    parser.add_argument("--n-episodes", type=int, default=100, help="Number of episodes")
    parser.add_argument("--max-steps", type=int, default=500, help="Max steps per episode")
    
    args = parser.parse_args()
    
    try:
        run_simulation(args)
        sys.exit(0)
    except MemoryError as e:
        print(f"Memory limit exceeded: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()