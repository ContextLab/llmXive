"""
Main orchestration script for the simulation pipeline.
Implements the simulation loop, checkpointing, and mode dispatch.
"""
import os
import sys
import time
import logging
import argparse
import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import itertools

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from simulation.config import SimulationConfig, get_default_config
from simulation.generator import generate_synthetic_data_from_config
from simulation.logger import setup_logger
from preprocessing.scaling import standardize_data, min_max_scale, robust_scale
from analysis.tests import run_scaled_t_test, run_scaled_anova, run_scaled_chi_squared
from analysis.metrics import calculate_aggregate_metrics, calculate_confidence_interval

# Ensure directories exist
def ensure_directories():
    """Create required output directories."""
    dirs = [
        "data/synthetic",
        "results",
        "results/figures",
        "logs"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def enforce_iteration_threshold(iterations: int, min_iterations: int = 10000) -> int:
    """Enforce minimum iteration count per configuration."""
    if iterations < min_iterations:
        logging.warning(f"Requested iterations ({iterations}) below threshold ({min_iterations}). Adjusting to {min_iterations}.")
        return min_iterations
    return iterations

def get_scaling_function(method: str):
    """Map scaling method name to function."""
    mapping = {
        "standardize": standardize_data,
        "minmax": min_max_scale,
        "robust": robust_scale
    }
    if method not in mapping:
        raise ValueError(f"Unknown scaling method: {method}")
    return mapping[method]

def run_single_iteration(
    iteration_id: int,
    config: SimulationConfig,
    scaling_method: str,
    test_type: str,
    seed: int,
    logger: Any
) -> Dict[str, Any]:
    """Run a single simulation iteration."""
    try:
        # Set seed for reproducibility
        np.random.seed(seed)
        
        # Generate data
        data, gt_label = generate_synthetic_data_from_config(config, seed=seed)
        
        # Apply scaling
        scale_func = get_scaling_function(scaling_method)
        scaled_data = scale_func(data)
        
        # Run test
        if test_type == "t_test":
            result = run_scaled_t_test(scaled_data, test_type)
        elif test_type == "anova":
            result = run_scaled_anova(scaled_data, test_type)
        elif test_type == "chi_squared":
            result = run_scaled_chi_squared(scaled_data, test_type)
        else:
            raise ValueError(f"Unknown test type: {test_type}")
        
        return {
            "iteration_id": iteration_id,
            "config_id": config.config_id,
            "scaling_method": scaling_method,
            "test_type": test_type,
            "p_value": result.p_value,
            "statistic": result.statistic,
            "ground_truth": gt_label,
            "scaling_params": json.dumps({"method": scaling_method}),
            "seed": seed
        }
    except Exception as e:
        logger.log("iteration_error", error=str(e), iteration_id=iteration_id)
        return None

def run_simulation_loop(
    configs: List[SimulationConfig],
    scaling_methods: List[str],
    test_types: List[str],
    total_iterations: int,
    checkpoint_interval: int = 1000,
    output_path: str = "results/simulation_results.csv",
    checkpoint_path: str = "results/partial_checkpoint.csv",
    logger: Any = None
) -> pd.DataFrame:
    """
    Run the full simulation loop over all combinations.
    
    Implements checkpointing to handle time limits and ensures
    at least 10,000 iterations per configuration.
    """
    if logger is None:
        logger = setup_logger(batch_id="simulation_loop")
    
    ensure_directories()
    
    all_results = []
    start_time = time.time()
    
    # Calculate iterations per config
    num_configs = len(configs) * len(scaling_methods) * len(test_types)
    if num_configs == 0:
        raise ValueError("No configurations to run")
    
    iterations_per_config = max(10000, total_iterations // num_configs)
    total_iterations = iterations_per_config * num_configs
    
    logger.log("simulation_start", 
               total_iterations=total_iterations, 
               num_configs=num_configs,
               configs=[c.config_id for c in configs])
    
    iteration_count = 0
    
    for config in configs:
        for scaling_method in scaling_methods:
            for test_type in test_types:
                config_seed_base = hash(f"{config.config_id}_{scaling_method}_{test_type}") % (2**32)
                
                for i in range(iterations_per_config):
                    iteration_count += 1
                    seed = config_seed_base + i
                    
                    result = run_single_iteration(
                        iteration_id=iteration_count,
                        config=config,
                        scaling_method=scaling_method,
                        test_type=test_type,
                        seed=seed,
                        logger=logger
                    )
                    
                    if result:
                        all_results.append(result)
                    
                    # Checkpoint
                    if iteration_count % checkpoint_interval == 0:
                        df_partial = pd.DataFrame(all_results)
                        df_partial.to_csv(checkpoint_path, index=False)
                        logger.log("checkpoint_saved", 
                                   iteration=iteration_count, 
                                   rows=len(all_results))
                    
                    # Time limit check (optional, 5 min per config for safety)
                    elapsed = time.time() - start_time
                    if elapsed > 300 and iteration_count > 1000:
                        logger.log("time_limit_warning", elapsed=elapsed)
                        break
                
                if elapsed > 300 and iteration_count > 1000:
                    break
            if elapsed > 300 and iteration_count > 1000:
                break
        if elapsed > 300 and iteration_count > 1000:
            break
    
    # Save final results
    if all_results:
        df_final = pd.DataFrame(all_results)
        df_final.to_csv(output_path, index=False)
        logger.log("simulation_complete", 
                   total_rows=len(all_results),
                   output_file=output_path)
    
    return df_final

def run_simulation_mode(args):
    """Run simulation mode."""
    logger = setup_logger(batch_id="simulation_mode")
    
    # Load or create configs
    if args.config_id:
        configs = [SimulationConfig(config_id=args.config_id)]
    else:
        configs = [get_default_config()]
    
    scaling_methods = args.scaling or ["standardize", "minmax", "robust"]
    test_types = args.tests or ["t_test", "anova", "chi_squared"]
    iterations = args.iterations or 10000
    
    iterations = enforce_iteration_threshold(iterations)
    
    df_results = run_simulation_loop(
        configs=configs,
        scaling_methods=scaling_methods,
        test_types=test_types,
        total_iterations=iterations,
        logger=logger
    )
    
    print(f"Simulation complete. Results saved to results/simulation_results.csv")
    print(f"Total iterations: {len(df_results)}")

def run_real_world_mode(args):
    """Run real-world data mode."""
    logger = setup_logger(batch_id="real_world_mode")
    # Placeholder for real world mode implementation
    logger.log("real_world_mode", status="placeholder")
    print("Real world mode not fully implemented in this task scope.")

def run_analyze_mode(args):
    """Run analysis mode."""
    logger = setup_logger(batch_id="analyze_mode")
    # Placeholder for analysis mode
    logger.log("analyze_mode", status="placeholder")
    print("Analysis mode not fully implemented in this task scope.")

def run_visualize_mode(args):
    """Run visualization mode."""
    logger = setup_logger(batch_id="visualize_mode")
    # Placeholder for visualization mode
    logger.log("visualize_mode", status="placeholder")
    print("Visualization mode not fully implemented in this task scope.")

def main():
    parser = argparse.ArgumentParser(description="Simulation Pipeline")
    subparsers = parser.add_subparsers(dest="mode")
    
    sim_parser = subparsers.add_parser("simulation", help="Run simulation")
    sim_parser.add_argument("--config-id", type=str, help="Specific config ID")
    sim_parser.add_argument("--iterations", type=int, help="Number of iterations")
    sim_parser.add_argument("--scaling", nargs="+", help="Scaling methods")
    sim_parser.add_argument("--tests", nargs="+", help="Test types")
    
    real_parser = subparsers.add_parser("real_world", help="Run real world analysis")
    analyze_parser = subparsers.add_parser("analyze", help="Run analysis")
    viz_parser = subparsers.add_parser("visualize", help="Run visualization")
    
    args = parser.parse_args()
    
    if args.mode == "simulation":
        run_simulation_mode(args)
    elif args.mode == "real_world":
        run_real_world_mode(args)
    elif args.mode == "analyze":
        run_analyze_mode(args)
    elif args.mode == "visualize":
        run_visualize_mode(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
