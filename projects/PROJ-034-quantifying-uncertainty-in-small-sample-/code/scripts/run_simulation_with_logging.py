"""
Script to run a simulation batch with logging as per T017.
This script demonstrates the logging functionality by running a single simulation
and writing the parameters to data/results/simulation.log.
"""
import os
import sys
import time
import argparse

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from simulation.config import SimulationConfig
from simulation.engine import generate_dataset, save_dataset_instance, calculate_vif
from simulation.logging_utils import log_simulation_run

def main():
    parser = argparse.ArgumentParser(description="Run simulation with logging")
    parser.add_argument("--N", type=int, default=20, help="Sample size")
    parser.add_argument("--rho", type=float, default=0.5, help="Target correlation")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--predictors", type=int, default=3, help="Number of predictors")
    parser.add_argument("--noise_std", type=float, default=1.0, help="Noise standard deviation")
    args = parser.parse_args()

    print(f"Starting simulation with N={args.N}, rho={args.rho}, seed={args.seed}")
    start_time = time.time()

    # Create config
    config = SimulationConfig(
        N=args.N,
        predictors=args.predictors,
        rho=args.rho,
        seed=args.seed,
        noise_std=args.noise_std
    )

    # Generate dataset
    dataset = generate_dataset(config)

    # Calculate VIF
    vif_values = calculate_vif(dataset.X)
    vif_max = max(vif_values) if vif_values else 0.0

    # Save dataset instance
    output_path = f"data/simulated/dataset_N{args.N}_rho{args.rho}_seed{args.seed}.json"
    save_dataset_instance(dataset, output_path)

    end_time = time.time()
    duration = end_time - start_time

    # Log the run
    log_simulation_run(
        N=args.N,
        rho=args.rho,
        seed=args.seed,
        duration=duration,
        vif_max=vif_max
    )

    print(f"Simulation completed in {duration:.2f}s. VIF max: {vif_max:.2f}")
    print(f"Dataset saved to: {output_path}")
    print(f"Log entry written to: data/results/simulation.log")

if __name__ == "__main__":
    main()