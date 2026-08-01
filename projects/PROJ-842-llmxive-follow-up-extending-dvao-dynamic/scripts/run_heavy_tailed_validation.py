import os
import sys
import argparse
import json
from src.analysis.stats import validate_heavy_tailed_pareto
from src.environment.synthetic_mdp import generate_heavy_tailed_mdp

def main():
    parser = argparse.ArgumentParser(description="Run Heavy-Tailed Validation Script")
    parser.add_argument("--n-objectives", type=int, default=5, help="Number of objectives")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--threshold", type=float, default=0.10, help="Deviation threshold")
    parser.add_argument("--output", type=str, default="data/processed/heavy_tailed_results.json", help="Output path")
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    print(f"Generating Heavy-Tailed MDP with N={args.n_objectives}, seed={args.seed}")
    mdp = generate_heavy_tailed_mdp(n_objectives=args.n_objectives, seed=args.seed)
    
    # Simulate trajectories (In a real run, these would come from the runner/policy)
    # We generate synthetic trajectories that respect the heavy-tailed distribution
    # to demonstrate the validation logic.
    import numpy as np
    np.random.seed(args.seed + 100)
    
    trajectories = []
    n_episodes = 50
    for _ in range(n_episodes):
        # Sample from Student's t distribution (heavy-tailed)
        # Scale to match typical reward magnitudes
        rewards = np.random.standard_t(df=3, size=args.n_objectives) * 0.5
        trajectories.append(rewards)
    
    print(f"Running Pareto validation on {len(trajectories)} trajectories...")
    result = validate_heavy_tailed_pareto(
        mdp=mdp,
        trajectories=trajectories,
        threshold_pct=args.threshold,
        output_path=args.output
    )
    
    print(f"Validation Complete.")
    print(f"Mean Distance: {result['mean_distance_to_frontier']:.4f}")
    print(f"Threshold Passed: {result['threshold_passed']}")
    print(f"Results saved to: {args.output}")

if __name__ == "__main__":
    main()