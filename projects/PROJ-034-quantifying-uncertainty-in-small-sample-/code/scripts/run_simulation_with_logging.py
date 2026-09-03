import os
import sys
import time
import argparse
import json
from typing import List, Dict, Any

# Add project root to path if running as script
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from simulation.config import SimulationConfig
from simulation.engine import generate_dataset, save_dataset_instance, calculate_vif
from simulation.logging_utils import log_simulation_run

def run_single_replication_with_logging(
    config: SimulationConfig,
    seed: int,
    output_dir: str = "data/simulated"
) -> Dict[str, Any]:
    """
    Runs a single simulation replication, saves the dataset, and logs the parameters.

    Args:
        config: The simulation configuration.
        seed: The random seed for this replication.
        output_dir: Directory to save the dataset instance.

    Returns:
        A dictionary containing the results of the replication including timing and VIF.
    """
    start_time = time.time()
    
    # Generate dataset
    dataset = generate_dataset(config, seed)
    
    # Save dataset instance
    dataset_path = save_dataset_instance(dataset, output_dir, seed)
    
    # Calculate max VIF for logging (re-calculate or retrieve from dataset if stored)
    # The generate_dataset function in engine.py should return a dict with vif_scores
    if hasattr(dataset, 'vif_scores') and dataset.vif_scores:
        vif_max = max(dataset.vif_scores.values())
    else:
        # Fallback if vif_scores not directly on dataset object but needs calculation
        # Assuming dataset.X is available
        vif_max = calculate_vif(dataset.X) if hasattr(dataset, 'X') and dataset.X is not None else 0.0
    
    duration = time.time() - start_time

    # Log the run
    log_simulation_run(
        N=config.n_samples,
        rho=config.correlation,
        seed=seed,
        duration=duration,
        vif_max=vif_max
    )

    return {
        "seed": seed,
        "path": dataset_path,
        "duration": duration,
        "vif_max": vif_max,
        "success": True
    }

def main():
    parser = argparse.ArgumentParser(description="Run a single simulation replication with logging.")
    parser.add_argument("--n-samples", type=int, default=30, help="Number of samples (N)")
    parser.add_argument("--correlation", type=float, default=0.5, help="Target correlation (rho)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output-dir", type=str, default="data/simulated", help="Output directory for datasets")
    
    args = parser.parse_args()

    config = SimulationConfig(
        n_samples=args.n_samples,
        n_predictors=3,
        correlation=args.correlation,
        noise_std=1.0,
        true_coefficients=[1.0, 2.0, -1.5]
    )

    try:
        result = run_single_replication_with_logging(config, args.seed, args.output_dir)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error during replication: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()