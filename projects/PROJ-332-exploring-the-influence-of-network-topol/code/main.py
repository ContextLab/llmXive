"""
Main entry point for the thermal conductivity simulation pipeline.
Orchestrates network generation, thermal solving, regression analysis, and sensitivity checks.
"""

import os
import sys
import csv
import logging
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

import numpy as np
import networkx as nx

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import SimulationConfig, load_config, get_simulation_parameters
from generate_networks import (
    generate_nanowire_network,
    calculate_average_degree,
    calculate_average_shortest_path_length,
    calculate_clustering_coefficient
)
from thermal_solver import calculate_effective_conductivity
from regression_analysis import (
    run_ols_regression,
    calculate_correlation_matrix,
    detect_percolation_threshold,
    update_csv_with_percolation_threshold,
    analyze_scaling_law
)
from sensitivity_analysis import (
    run_sensitivity_sweep,
    calculate_deviation_report,
    report_sensitivity_results,
    analyze_sensitivity
)
from material_db import get_material_conductivity
from update_state import update_state

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('simulation_pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
RUNTIME_CEILING_HOURS = 6
RUNTIME_CEILING_SECONDS = RUNTIME_CEILING_HOURS * 3600

def load_existing_results(csv_path: str) -> List[Dict[str, Any]]:
    """
    Load existing results from CSV file.
    
    Args:
        csv_path: Path to the results CSV file
        
    Returns:
        List of result dictionaries
    """
    if not os.path.exists(csv_path):
        return []
        
    results = []
    with open(csv_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            numeric_fields = ['seed', 'N', 'p', 'avg_degree', 'conductivity', 
                             'percolation_flag', 'scaling_factor',
                             'regression_slope', 'regression_p_value', 'regression_r_squared',
                             'sensitivity_mean', 'sensitivity_std', 'sensitivity_deviation']
            
            result = {}
            for key, value in row.items():
                if key in numeric_fields:
                    try:
                        result[key] = float(value)
                    except (ValueError, TypeError):
                        result[key] = value
                else:
                    result[key] = value
            results.append(result)
            
    return results

def append_results_to_csv(results: List[Dict[str, Any]], csv_path: str) -> None:
    """
    Append results to CSV file.
    
    Args:
        results: List of result dictionaries
        csv_path: Path to the results CSV file
    """
    fieldnames = [
        'seed', 'N', 'p', 'avg_degree', 'conductivity',
        'percolation_flag', 'scaling_factor',
        'regression_slope', 'regression_p_value', 'regression_r_squared',
        'sensitivity_mean', 'sensitivity_std', 'sensitivity_deviation'
    ]
    
    # Create file with headers if it doesn't exist
    if not os.path.exists(csv_path):
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
    
    # Append results
    with open(csv_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        for result in results:
            # Ensure all fields are present
            row = {k: result.get(k, '') for k in fieldnames}
            writer.writerow(row)

def run_simulation(config: SimulationConfig, results_file: str) -> Dict[str, Any]:
    """
    Run a single simulation iteration.
    
    Args:
        config: Simulation configuration
        results_file: Path to output CSV file
        
    Returns:
        Dictionary containing simulation results
    """
    start_time = time.time()
    
    logger.info(f"Starting simulation: N={config.N}, p={config.p}, "
               f"d={config.d*1e9:.1f}nm, material={config.material}")
    
    # Step 1: Generate network (US1)
    try:
        graph = generate_nanowire_network(
            N=config.N,
            p=config.p,
            seed=config.seed,
            target_degree=config.target_degree
        )
    except Exception as e:
        logger.error(f"Network generation failed: {e}")
        raise
    
    # Calculate graph metrics (US2)
    avg_degree = calculate_average_degree(graph)
    avg_path_length = calculate_average_shortest_path_length(graph)
    clustering_coef = calculate_clustering_coefficient(graph)
    
    # Step 2: Compute thermal conductivity (US1)
    try:
        conductivity = calculate_effective_conductivity(
            graph,
            material=config.material,
            diameter=config.d,
            length=config.l
        )
    except Exception as e:
        logger.error(f"Thermal solving failed: {e}")
        raise
    
    # Check for disconnected graph
    num_components = len(list(nx.connected_components(graph)))
    percolation_flag = 1 if num_components == 1 else 0
    
    if num_components > 1:
        logger.warning(f"Graph disconnected ({num_components} components); "
                     f"conductivity set to 0.0")
        conductivity = 0.0
    
    # Step 3: Sensitivity analysis (US3)
    try:
        sensitivity_results = run_sensitivity_sweep(
            base_config=config,
            parameter="diameter",
            sweep_range=[config.d * 0.9, config.d, config.d * 1.1],
            num_repeats=2
        )
        
        sensitivity_mean = sensitivity_results["mean_conductivity"]
        sensitivity_std = sensitivity_results["std_conductivity"]
        sensitivity_deviation = sensitivity_results["deviation_percent"]
    except Exception as e:
        logger.warning(f"Sensitivity analysis failed: {e}")
        sensitivity_mean = conductivity
        sensitivity_std = 0.0
        sensitivity_deviation = 0.0
    
    # Step 4: Compile results
    result = {
        "seed": config.seed,
        "N": config.N,
        "p": config.p,
        "avg_degree": avg_degree,
        "conductivity": conductivity,
        "percolation_flag": percolation_flag,
        "scaling_factor": sensitivity_mean / conductivity if conductivity > 0 else 0.0,
        "regression_slope": None,  # Will be updated in batch analysis
        "regression_p_value": None,
        "regression_r_squared": None,
        "sensitivity_mean": sensitivity_mean,
        "sensitivity_std": sensitivity_std,
        "sensitivity_deviation": sensitivity_deviation
    }
    
    elapsed = time.time() - start_time
    logger.info(f"Simulation completed in {elapsed:.2f}s: "
               f"conductivity={conductivity:.2f} W/(m·K)")
    
    return result

def main():
    """
    Main entry point for the simulation pipeline.
    Runs a grid of simulations and performs regression analysis.
    """
    logger.info("Starting thermal conductivity simulation pipeline")
    pipeline_start = time.time()
    
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Define simulation grid
    N_values = config.N_values if hasattr(config, 'N_values') else [50, 100]
    p_values = config.p_values if hasattr(config, 'p_values') else [0.1, 0.15, 0.2]
    seeds = config.seeds if hasattr(config, 'seeds') else [42, 123, 456]
    
    results_file = config.results_file if hasattr(config, 'results_file') else \
                  os.path.join(project_root, "data", "processed", "simulation_results.csv")
    
    # Load existing results
    existing_results = load_existing_results(results_file)
    logger.info(f"Loaded {len(existing_results)} existing results")
    
    # Run simulations
    all_results = []
    
    for N in N_values:
        for p in p_values:
            for seed in seeds:
                # Check runtime ceiling (US1 - FR-008)
                elapsed = time.time() - pipeline_start
                if elapsed > RUNTIME_CEILING_SECONDS:
                    logger.error("Runtime ceiling (6h) exceeded. Aborting grid.")
                    sys.exit(1)
                
                sim_config = SimulationConfig(
                    N=N,
                    p=p,
                    d=config.d,
                    l=config.l,
                    material=config.material,
                    seed=seed,
                    target_degree=config.target_degree
                )
                
                try:
                    result = run_simulation(sim_config, results_file)
                    all_results.append(result)
                except Exception as e:
                    logger.error(f"Simulation failed for N={N}, p={p}, seed={seed}: {e}")
                    continue
    
    # Append new results to CSV
    if all_results:
        append_results_to_csv(all_results, results_file)
        logger.info(f"Appended {len(all_results)} new results to {results_file}")
        
        # Update state
        try:
            update_state(
                artifact_name="simulation_results.csv",
                artifact_path=results_file,
                task_id="T039"
            )
            logger.info("State updated successfully")
        except Exception as e:
            logger.warning(f"Failed to update state: {e}")
    
    # Step 5: Regression analysis (US2)
    if len(all_results) > 1:
        try:
            # Prepare data for regression
            df = pd.DataFrame(all_results)
            x_data = df['avg_degree'].values
            y_data = df['conductivity'].values
            
            # Run regression
            regression_results = run_ols_regression(x_data, y_data)
            
            # Update results with regression data
            for result in all_results:
                result['regression_slope'] = regression_results['slope']
                result['regression_p_value'] = regression_results['p_value']
                result['regression_r_squared'] = regression_results['r_squared']
            
            # Re-append with updated regression data
            append_results_to_csv(all_results, results_file)
            logger.info("Regression analysis completed and results updated")
            
            # Detect percolation threshold
            percolation_threshold = detect_percolation_threshold(
                df['avg_degree'].values,
                df['percolation_flag'].values
            )
            logger.info(f"Percolation threshold detected at avg_degree={percolation_threshold}")
            
        except Exception as e:
            logger.error(f"Regression analysis failed: {e}")
    
    total_elapsed = time.time() - pipeline_start
    logger.info(f"Pipeline completed in {total_elapsed:.2f}s")
    logger.info(f"Total results: {len(all_results)}")

if __name__ == "__main__":
    import pandas as pd
    main()