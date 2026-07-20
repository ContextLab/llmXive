import os
import sys
import time
import argparse
from typing import List, Dict, Any

# Add parent to path for imports if running as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.config import SimulationConfig
from simulation.engine import generate_dataset, save_dataset_instance, calculate_vif
from simulation.logging_utils import log_simulation_run

def run_single_replication_with_logging(config: SimulationConfig, instance_id: str) -> Dict[str, Any]:
    """
    Run a single simulation replication and log the parameters and results.
    
    Args:
        config: The simulation configuration.
        instance_id: Unique identifier for this run.
        
    Returns:
        A dictionary containing the results and metadata.
    """
    start_time = time.time()
    
    # Generate dataset
    dataset = generate_dataset(
        N=config.N,
        predictors=config.predictors,
        correlation_matrix=config.correlation_matrix,
        noise_std=config.noise,
        true_coefficients=config.true_coefficients,
        seed=config.seed
    )
    
    # Calculate VIF
    vif_values = calculate_vif(dataset.X)
    vif_max = max(vif_values) if vif_values else 0.0
    
    # Save dataset instance
    save_dataset_instance(dataset, instance_id)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Log the run
    log_simulation_run(
        N=config.N,
        rho=float(config.correlation_matrix[0][1]) if config.predictors >= 2 and config.correlation_matrix is not None else 0.0,
        seed=config.seed,
        duration=duration,
        vif_max=vif_max,
        config_path=config.__dict__.get('config_path', None),
        instance_id=instance_id
    )
    
    return {
        "instance_id": instance_id,
        "N": config.N,
        "rho": config.correlation_matrix[0][1] if config.predictors >= 2 and config.correlation_matrix is not None else 0.0,
        "seed": config.seed,
        "duration": duration,
        "vif_max": vif_max,
        "status": "success"
    }

def main():
    parser = argparse.ArgumentParser(description="Run simulation with logging.")
    parser.add_argument("--N", type=int, default=30, help="Sample size")
    parser.add_argument("--predictors", type=int, default=3, help="Number of predictors")
    parser.add_argument("--rho", type=float, default=0.5, help="Target correlation")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--noise", type=float, default=1.0, help="Noise standard deviation")
    parser.add_argument("--instance-id", type=str, default="test_run_001", help="Instance ID")
    
    args = parser.parse_args()
    
    # Construct correlation matrix based on rho (simple equicorrelation for demo)
    # In a real scenario, this might be more complex or loaded from config
    import numpy as np
    if args.predictors > 1:
        corr_mat = np.full((args.predictors, args.predictors), args.rho)
        np.fill_diagonal(corr_mat, 1.0)
    else:
        corr_mat = np.array([[1.0]])
    
    # Define true coefficients (simple case: all 1.0)
    true_coeffs = np.ones(args.predictors)
    
    config = SimulationConfig(
        N=args.N,
        predictors=args.predictors,
        correlation_matrix=corr_mat,
        noise=args.noise,
        true_coefficients=true_coeffs,
        seed=args.seed
    )
    
    result = run_single_replication_with_logging(config, args.instance_id)
    print(f"Simulation run completed: {result['instance_id']}")
    print(f"Duration: {result['duration']:.2f}s, Max VIF: {result['vif_max']:.2f}")

if __name__ == "__main__":
    main()
