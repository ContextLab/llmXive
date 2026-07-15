import os
import sys
import csv
import logging
import time
import argparse
from typing import List, Dict, Any, Optional
from datetime import datetime

from config import SimulationConfig, load_config, get_simulation_parameters
from generate_networks import generate_nanowire_network, calculate_average_degree, generate_network_grid
from thermal_solver import solve_kirchhoff_heat_flow, calculate_effective_conductivity, calculate_fuchs_sondheimer_factor
from material_db import get_material_conductivity
from regression_analysis import run_ols_regression, detect_percolation_threshold, analyze_scaling_law
from sensitivity_analysis import run_sensitivity_sweep, calculate_deviation_report

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
RUNTIME_LIMIT_SECONDS = 6 * 60 * 60  # 6 hours
CSV_FIELDNAMES = [
    'seed', 'N', 'p', 'avg_degree', 'conductivity', 'percolation_flag', 
    'scaling_factor', 'd', 'l', 'material', 'target_degree', 
    'shortest_path', 'clustering_coeff', 'percolation_threshold',
    'regression_exponent', 'regression_p_value', 'sensitivity_deviation'
]

def load_existing_results(filepath: str) -> List[Dict[str, Any]]:
    """Load existing results from CSV if it exists."""
    results = []
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Convert numeric fields
                    numeric_fields = ['N', 'p', 'avg_degree', 'conductivity', 'd', 'l', 
                                    'target_degree', 'shortest_path', 'clustering_coeff',
                                    'percolation_threshold', 'regression_exponent', 
                                    'regression_p_value', 'sensitivity_deviation']
                    for field in numeric_fields:
                        if field in row and row[field]:
                            try:
                                row[field] = float(row[field])
                            except ValueError:
                                pass
                    results.append(row)
            logger.info(f"Loaded {len(results)} existing results")
        except Exception as e:
            logger.warning(f"Failed to load existing results: {e}")
    else:
        logger.info("No existing results file found, starting fresh")
    return results

def append_results_to_csv(filepath: str, results: List[Dict[str, Any]]) -> None:
    """Append results to CSV file, creating it if necessary."""
    if not results:
        return
    
    # Ensure file exists with headers
    file_exists = os.path.exists(filepath)
    
    with open(filepath, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Appended {len(results)} results to {filepath}")

def run_single_simulation(config: SimulationConfig, seed: Optional[int] = None) -> Dict[str, Any]:
    """Run a single simulation with given parameters."""
    if seed is not None:
        config.seed = seed
    
    start_time = time.time()
    
    try:
        # Generate network
        logger.info(f"Generating network: N={config.N}, p={config.p}, seed={config.seed}")
        G = generate_nanowire_network(
            N=config.N,
            p=config.p,
            seed=config.seed,
            target_degree=config.target_degree
        )
        
        # Calculate graph metrics
        avg_degree = calculate_average_degree(G)
        shortest_path = calculate_average_shortest_path_length(G) if len(G) > 1 else 0.0
        clustering = calculate_clustering_coefficient(G)
        
        # Check for disconnected graph
        percolation_flag = nx.is_connected(G) if len(G) > 1 else False
        if not percolation_flag and len(G) > 1:
            logger.warning("Graph disconnected; conductivity set to 0.0")
            conductivity = 0.0
        else:
            # Get material conductivity
            bulk_k = get_material_conductivity(config.material)
            
            # Calculate Fuchs-Sondheimer factor
            fs_factor = calculate_fuchs_sondheimer_factor(
                d=config.d,
                lambda_bulk=config.lambda_bulk,
                p_specular=config.p_specular
            )
            
            # Assign thermal resistance and solve
            effective_k = calculate_effective_conductivity(
                G, bulk_k, config.d, config.l, fs_factor
            )
            conductivity = effective_k
        
        elapsed = time.time() - start_time
        
        result = {
            'seed': config.seed,
            'N': config.N,
            'p': config.p,
            'avg_degree': avg_degree,
            'conductivity': conductivity,
            'percolation_flag': int(percolation_flag),
            'scaling_factor': 1.0,  # Placeholder for future use
            'd': config.d,
            'l': config.l,
            'material': config.material,
            'target_degree': config.target_degree,
            'shortest_path': shortest_path,
            'clustering_coeff': clustering,
            'percolation_threshold': None,
            'regression_exponent': None,
            'regression_p_value': None,
            'sensitivity_deviation': None
        }
        
        logger.info(f"Simulation completed in {elapsed:.2f}s: k={conductivity:.4f}")
        return result
        
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise

def run_grid_simulation(config: SimulationConfig) -> List[Dict[str, Any]]:
    """Run simulations across a grid of parameters with timeout check."""
    results = []
    start_time = time.time()
    
    logger.info(f"Starting grid simulation: N=[{config.N_min}, {config.N_max}], p=[{config.p_min}, {config.p_max}]")
    
    # Generate grid parameters
    N_values = [int(config.N_min + i * (config.N_max - config.N_min) / (config.N_steps - 1)) 
               for i in range(config.N_steps)]
    p_values = [config.p_min + i * (config.p_max - config.p_min) / (config.p_steps - 1) 
               for i in range(config.p_steps)]
    
    grid_params = []
    for N in N_values:
        for p in p_values:
            for seed in range(3):  # 3 seeds per configuration
                grid_params.append({'N': N, 'p': p, 'seed': seed})
    
    logger.info(f"Running {len(grid_params)} simulations")
    
    for i, params in enumerate(grid_params):
        # Global Timer Check
        elapsed = time.time() - start_time
        if elapsed > RUNTIME_LIMIT_SECONDS:
            logger.error("Runtime ceiling (6h) exceeded. Aborting grid.")
            sys.exit(1)
        
        logger.info(f"[{i+1}/{len(grid_params)}] Running N={params['N']}, p={params['p']:.3f}, seed={params['seed']}")
        
        try:
            sim_config = SimulationConfig(
                N=params['N'],
                p=params['p'],
                d=config.d,
                l=config.l,
                seed=params['seed'],
                material=config.material,
                target_degree=config.target_degree,
                lambda_bulk=config.lambda_bulk,
                p_specular=config.p_specular,
                timeout_seconds=config.timeout_seconds
            )
            
            result = run_single_simulation(sim_config)
            results.append(result)
            
        except Exception as e:
            logger.error(f"Failed simulation {i+1}: {e}")
            # Continue with next simulation
            continue
    
    logger.info(f"Grid simulation completed. Total time: {time.time() - start_time:.2f}s")
    return results

def run_sensitivity_analysis(config: SimulationConfig, base_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run sensitivity analysis on existing results."""
    if not base_results:
        logger.warning("No base results for sensitivity analysis")
        return []
    
    logger.info("Starting sensitivity analysis")
    
    # Run sensitivity sweep
    sensitivity_results = run_sensitivity_sweep(base_results, config)
    
    # Calculate deviation report
    deviation_report = calculate_deviation_report(sensitivity_results)
    
    # Update base results with sensitivity metrics
    for i, result in enumerate(base_results):
        if i < len(deviation_report):
            result['sensitivity_deviation'] = deviation_report[i]['deviation']
    
    logger.info("Sensitivity analysis completed")
    return base_results

def main():
    """Main entry point for the simulation pipeline."""
    parser = argparse.ArgumentParser(description="Thermal Conductivity Simulation Pipeline")
    parser.add_argument('--run-single', action='store_true', help="Run single simulation")
    parser.add_argument('--run-grid', action='store_true', help="Run grid simulation")
    parser.add_argument('--sensitivity-only', action='store_true', help="Run sensitivity analysis only")
    parser.add_argument('--seed', type=int, default=42, help="Random seed for single simulation")
    parser.add_argument('--config', type=str, help="Path to config file (not implemented)")
    
    args = parser.parse_args()
    
    logger.info("Starting thermal conductivity simulation pipeline")
    
    # Load configuration
    config = load_config()
    logger.info(f"Configuration loaded: {get_simulation_parameters()}")
    
    # Ensure output directory exists
    os.makedirs(config.output_dir, exist_ok=True)
    results_file = os.path.join(config.output_dir, config.results_file)
    
    # Load existing results
    existing_results = load_existing_results(results_file)
    
    try:
        if args.run_single:
            logger.info("Running single simulation")
            result = run_single_simulation(config, seed=args.seed)
            append_results_to_csv(results_file, [result])
            
        elif args.run_grid:
            logger.info("Running grid simulation")
            new_results = run_grid_simulation(config)
            append_results_to_csv(results_file, new_results)
            
            # Optional: Run regression analysis on new results
            if new_results:
                logger.info("Running regression analysis on new results")
                # This would integrate with T029
                
        elif args.sensitivity_only:
            logger.info("Running sensitivity analysis")
            updated_results = run_sensitivity_analysis(config, existing_results)
            append_results_to_csv(results_file, updated_results)
            
        else:
            logger.error("No action specified. Use --run-single, --run-grid, or --sensitivity-only")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
