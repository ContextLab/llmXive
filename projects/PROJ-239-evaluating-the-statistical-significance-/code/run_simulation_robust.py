"""Script to run robust simulation and save results."""
import argparse
import logging
import sys
import os
import warnings
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.config import load_config, parse_cli_args, validate_config
from code.simulation_runner import run_robust_simulation

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Run robust simulation')
    parser.add_argument('--icc', type=float, required=True, help='ICC value')
    parser.add_argument('--iterations', type=int, default=1000, help='Number of iterations')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--n-clusters', type=int, default=100, help='Number of clusters')
    parser.add_argument('--n-obs-per-cluster', type=int, default=100, help='Observations per cluster')
    parser.add_argument('--alpha', type=float, default=0.05, help='Significance level')
    parser.add_argument('--n-permutations', type=int, default=1000, help='Number of permutations')
    parser.add_argument('--output', type=str, default='data/derived/robustResults.csv',
                        help='Output path for results')
    return parser.parse_args()

def main():
    """Main entry point for robust simulation script."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    args = parse_args()
    
    # Load and configure
    cfg = load_config()
    cfg['icc_range'] = [args.icc]
    cfg['iterations'] = args.iterations
    cfg['seed'] = args.seed
    cfg['n_clusters'] = args.n_clusters
    cfg['n_obs_per_cluster'] = args.n_obs_per_cluster
    cfg['alpha_levels'] = [args.alpha]
    cfg['n_permutations'] = args.n_permutations
    cfg['output_robust'] = args.output
    
    validate_config(cfg)
    
    # Run simulation
    logging.info(f"Running robust simulation: ICC={args.icc}, iterations={args.iterations}")
    
    results = run_robust_simulation(
        icc=args.icc,
        n_iterations=args.iterations,
        seed=args.seed,
        n_clusters=args.n_clusters,
        n_obs_per_cluster=args.n_obs_per_cluster,
        alpha=args.alpha,
        n_permutations=args.n_permutations
    )
    
    # Save results
    import pandas as pd
    df = pd.DataFrame(results)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    df.to_csv(args.output, index=False)
    
    # Verify
    if not os.path.exists(args.output):
        raise RuntimeError(f"Output file not created: {args.output}")
    
    expected_rows = args.iterations * 2  # Two methods
    actual_rows = len(df)
    if actual_rows != expected_rows:
        logging.warning(f"Expected {expected_rows} rows, got {actual_rows}. Some iterations may have failed.")
    
    logging.info(f"Robust simulation completed. Results saved to {args.output}")
    print(f"Saved {actual_rows} results to {args.output}")

if __name__ == '__main__':
    main()