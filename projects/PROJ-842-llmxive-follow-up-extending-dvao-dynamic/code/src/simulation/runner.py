import argparse
import json
import os
import sys
import time
import traceback
import numpy as np
from datetime import datetime

# Ensure src is in path for local execution
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.simulation.synthetic_mdp import SyntheticTabularMDP
from src.simulation.heuristic import MovingWindowVarianceHeuristic
from src.analysis.pareto import distance_to_frontier, calculate_pareto_frontier
from src.config.defaults import load_defaults

def get_memory_usage_bytes():
    """
    Returns current memory usage in bytes.
    Uses psutil if available, otherwise returns 0.
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss
    except ImportError:
        return 0

def check_memory_limit(limit_gb=7.0):
    """
    Checks if current memory usage exceeds the limit.
    Returns True if within limit, False otherwise.
    """
    current_bytes = get_memory_usage_bytes()
    limit_bytes = limit_gb * 1024 * 1024 * 1024
    return current_bytes <= limit_bytes

def log_memory_usage():
    """Logs current memory usage to stderr."""
    current_bytes = get_memory_usage_bytes()
    current_gb = current_bytes / (1024 ** 3)
    print(f"[MEM] Current usage: {current_gb:.2f} GB", file=sys.stderr)

def run_simulation(n_objectives, seed, noise_correlation, k_window, rollout_size, output_path):
    """
    Executes a single simulation run for given parameters.
    
    Args:
        n_objectives: Number of objectives (N)
        seed: Random seed for determinism
        noise_correlation: Noise correlation parameter ρ
        k_window: Window size for heuristic
        rollout_size: Number of steps per episode
        output_path: Path to write empirical results JSON
    
    Returns:
        Dict containing simulation results
    """
    print(f"[RUN] Starting simulation: N={n_objectives}, ρ={noise_correlation}, k={k_window}, seed={seed}")
    
    # Initialize MDP
    mdp = SyntheticTabularMDP(
        n_objectives=n_objectives,
        seed=seed,
        noise_correlation=noise_correlation
    )
    
    # Initialize Heuristic
    heuristic = MovingWindowVarianceHeuristic(window_size=k_window)
    
    # Storage for results
    empirical_variances = []
    pareto_distances = []
    episode_rewards = []
    
    # Run episodes
    num_episodes = 10  # Fixed for memory constraints
    for ep in range(num_episodes):
        if not check_memory_limit():
            raise MemoryError(f"[RUN] Memory limit exceeded at episode {ep}")
        
        state = mdp.reset()
        episode_reward = 0.0
        
        for t in range(rollout_size):
            # Simple policy: random action
            action = mdp.action_space.sample()
            next_state, reward, done, info = mdp.step(action)
            
            # Update heuristic with reward
            heuristic.update(reward)
            
            # Collect empirical variance estimate from heuristic
            if len(heuristic.window) >= k_window:
                var_est = heuristic.get_variance_estimate()
                empirical_variances.append(var_est)
            
            # Calculate Pareto distance (using current state features and rewards)
            # For tabular MDP, we use the accumulated rewards as approximation
            if len(episode_rewards) > 0:
                # Calculate distance to frontier based on accumulated rewards
                current_frontier = calculate_pareto_frontier(episode_rewards)
                dist = distance_to_frontier(current_frontier, episode_rewards[-1])
                pareto_distances.append(dist)
            
            episode_rewards.append(reward)
            episode_reward += np.sum(reward)
            
            state = next_state
            if done:
                break
        
        print(f"[RUN] Episode {ep+1}/{num_episodes} completed. Total reward: {episode_reward:.4f}")
    
    # Calculate aggregate statistics
    if len(empirical_variances) > 0:
        avg_empirical_variance = float(np.mean(empirical_variances))
        std_empirical_variance = float(np.std(empirical_variances))
    else:
        avg_empirical_variance = 0.0
        std_empirical_variance = 0.0
    
    if len(pareto_distances) > 0:
        avg_pareto_distance = float(np.mean(pareto_distances))
        std_pareto_distance = float(np.std(pareto_distances))
    else:
        avg_pareto_distance = 0.0
        std_pareto_distance = 0.0
    
    # Prepare results
    results = {
        "n_objectives": n_objectives,
        "noise_correlation": noise_correlation,
        "k_window": k_window,
        "seed": seed,
        "num_episodes": num_episodes,
        "rollout_size": rollout_size,
        "empirical_variance": {
            "mean": avg_empirical_variance,
            "std": std_empirical_variance,
            "samples": len(empirical_variances)
        },
        "pareto_distance": {
            "mean": avg_pareto_distance,
            "std": std_pareto_distance,
            "samples": len(pareto_distances)
        },
        "timestamp": datetime.now().isoformat(),
        "memory_usage_gb": get_memory_usage_bytes() / (1024 ** 3)
    }
    
    # Write to output file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"[RUN] Results written to {output_path}")
    return results

def main():
    """
    Main entry point for simulation runner.
    Parses command line arguments and executes simulation.
    """
    parser = argparse.ArgumentParser(description='Run DVAO simulation experiments')
    parser.add_argument('--n-objectives', type=int, default=5,
                      help='Number of objectives (N)')
    parser.add_argument('--seed', type=int, default=42,
                      help='Random seed')
    parser.add_argument('--noise-correlation', type=float, default=0.0,
                      choices=[0.0, 0.2, 0.5],
                      help='Noise correlation parameter ρ')
    parser.add_argument('--k-window', type=int, default=10,
                      help='Window size for moving variance heuristic')
    parser.add_argument('--rollout-size', type=int, default=100,
                      help='Number of steps per episode')
    parser.add_argument('--output', type=str, default='data/processed/empirical_results.json',
                      help='Output path for results JSON')
    
    args = parser.parse_args()
    
    try:
        results = run_simulation(
            n_objectives=args.n_objectives,
            seed=args.seed,
            noise_correlation=args.noise_correlation,
            k_window=args.k_window,
            rollout_size=args.rollout_size,
            output_path=args.output
        )
        
        print(f"[SUCCESS] Simulation completed successfully")
        print(f"[RESULT] Empirical Variance: {results['empirical_variance']['mean']:.6f}")
        print(f"[RESULT] Pareto Distance: {results['pareto_distance']['mean']:.6f}")
        return 0
        
    except Exception as e:
        print(f"[ERROR] Simulation failed: {str(e)}", file=sys.stderr)
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())