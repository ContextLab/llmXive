import os
import sys
import csv
import logging
import time
import argparse
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import project modules
from config import SimulationConfig, load_config, get_simulation_parameters
from generate_networks import (
    generate_nanowire_network_for_degree,
    calculate_average_degree,
    calculate_average_shortest_path_length,
    calculate_clustering_coefficient,
    validate_degree_bounds,
    validate_connection_probability
)
from thermal_solver import (
    calculate_fuchs_sondheimer_factor,
    assign_thermal_resistance,
    build_edge_resistances,
    solve_kirchhoff_heat_flow,
    calculate_effective_conductivity
)
from material_db import get_material_conductivity, list_available_materials
from regression_analysis import (
    run_ols_regression,
    detect_percolation_threshold,
    analyze_scaling_law
)
from utils import setup_logging, write_csv_row, format_error
from update_state import main as update_state_main

logger = logging.getLogger(__name__)

# Global start time for runtime check
GLOBAL_START_TIME = time.time()
RUNTIME_LIMIT_SECONDS = 6 * 3600  # 6 hours

def check_runtime_limit():
    """Check if runtime limit has been exceeded."""
    elapsed = time.time() - GLOBAL_START_TIME
    if elapsed > RUNTIME_LIMIT_SECONDS:
        return True
    return False

def abort_on_timeout():
    """Abort execution if runtime limit exceeded."""
    if check_runtime_limit():
        logger.error("Runtime ceiling (6h) exceeded. Aborting grid.")
        sys.exit(1)

def load_existing_results(filepath: str) -> List[Dict[str, Any]]:
    """Load existing results from CSV if it exists."""
    results = []
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Convert numeric fields back to float/int
                    for key in ['seed', 'N', 'p', 'avg_degree', 'conductivity', 'percolation_flag']:
                        if key in row and row[key] != '':
                            try:
                                row[key] = float(row[key])
                                if key in ['seed', 'N', 'percolation_flag']:
                                    row[key] = int(row[key])
                            except ValueError:
                                pass
                    results.append(row)
            logger.info(f"Loaded {len(results)} existing results from {filepath}")
        except Exception as e:
            logger.warning(f"Could not load existing results: {e}")
    return results

def append_results_to_csv(filepath: str, results: List[Dict[str, Any]]):
    """Append results to CSV file."""
    if not results:
        logger.info("No results to append.")
        return

    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    # Check if file exists to determine if we need headers
    file_exists = os.path.exists(filepath) and os.path.getsize(filepath) > 0
    
    fieldnames = [
        'seed', 'N', 'p', 'avg_degree', 'conductivity', 
        'percolation_flag', 'scaling_factor', 'percolation_threshold',
        'regression_slope', 'regression_intercept', 'regression_r2',
        'regression_pvalue', 'regression_ci_lower', 'regression_ci_upper'
    ]

    with open(filepath, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for result in results:
            # Ensure all fields are present, defaulting to empty string
            row = {k: result.get(k, '') for k in fieldnames}
            writer.writerow(row)
    
    logger.info(f"Appended {len(results)} results to {filepath}")

def run_single_simulation(config: SimulationConfig, output_file: str) -> Optional[Dict[str, Any]]:
    """Run a single simulation and return results."""
    abort_on_timeout()
    
    try:
        N = config.N
        target_degree = config.target_degree
        seed = config.seed
        material = config.material
        bulk_k = config.bulk_k if hasattr(config, 'bulk_k') else None
        diameter = config.diameter if hasattr(config, 'diameter') else 50.0  # default 50nm
        length = config.length if hasattr(config, 'length') else 1000.0  # default 1um

        logger.info(f"Running simulation: N={N}, target_degree={target_degree}, seed={seed}")

        # Validate inputs
        validate_degree_bounds(target_degree, N)
        
        # Generate network
        G = generate_nanowire_network_for_degree(N, target_degree, seed)
        
        if G is None or len(G.nodes()) == 0:
            logger.warning(f"Failed to generate network for N={N}, target_degree={target_degree}")
            return None

        # Calculate graph metrics
        avg_degree = calculate_average_degree(G)
        avg_path_length = calculate_average_shortest_path_length(G)
        clustering_coef = calculate_clustering_coefficient(G)

        # Check percolation (largest connected component)
        if nx.is_connected(G):
            percolation_flag = 1
        else:
            largest_cc = max(nx.connected_components(G), key=len)
            percolation_flag = 1 if len(largest_cc) >= 0.8 * len(G) else 0
            if percolation_flag == 0:
                logger.warning(f"Graph disconnected; conductivity set to 0.0")

        # Get material conductivity
        k_bulk = get_material_conductivity(material, bulk_k)

        # Calculate size-correction factor (Fuchs-Sondheimer)
        fs_factor = calculate_fuchs_sondheimer_factor(diameter, k_bulk)

        # Assign thermal resistance and solve
        if percolation_flag == 0:
            effective_k = 0.0
        else:
            edge_resistances = assign_thermal_resistance(G, k_bulk, diameter, length)
            G_edge = build_edge_resistances(G, edge_resistances)
            effective_k = solve_kirchhoff_heat_flow(G_edge, diameter, length)

        # Run regression analysis if sufficient data points exist (simulated for single run)
        # For single run, we set regression fields to None or 0
        regression_slope = 0.0
        regression_intercept = 0.0
        regression_r2 = 0.0
        regression_pvalue = 1.0
        regression_ci_lower = 0.0
        regression_ci_upper = 0.0
        percolation_threshold = 0.0  # Calculated across grid, not single run

        result = {
            'seed': seed,
            'N': N,
            'p': G.number_of_edges() / (N * (N - 1) / 2) if N > 1 else 0.0,
            'avg_degree': avg_degree,
            'conductivity': effective_k,
            'percolation_flag': percolation_flag,
            'scaling_factor': fs_factor,
            'percolation_threshold': percolation_threshold,
            'regression_slope': regression_slope,
            'regression_intercept': regression_intercept,
            'regression_r2': regression_r2,
            'regression_pvalue': regression_pvalue,
            'regression_ci_lower': regression_ci_lower,
            'regression_ci_upper': regression_ci_upper
        }

        logger.info(f"Simulation complete: conductivity={effective_k:.4f} W/(m·K)")
        return result

    except Exception as e:
        logger.error(format_error(e))
        return None

def run_grid_simulation(config: SimulationConfig, output_file: str):
    """Run simulation grid over specified parameters."""
    abort_on_timeout()
    
    seeds = config.seeds if hasattr(config, 'seeds') else [42]
    N_values = config.N_values if hasattr(config, 'N_values') else [100]
    target_degrees = config.target_degrees if hasattr(config, 'target_degrees') else [3, 4, 5, 6]

    all_results = []

    for seed in seeds:
        for N in N_values:
            for target_degree in target_degrees:
                # Create config for this specific run
                run_config = SimulationConfig(
                    N=N,
                    target_degree=target_degree,
                    seed=seed,
                    material=config.material,
                    bulk_k=config.bulk_k if hasattr(config, 'bulk_k') else None,
                    diameter=config.diameter if hasattr(config, 'diameter') else 50.0,
                    length=config.length if hasattr(config, 'length') else 1000.0
                )
                
                result = run_single_simulation(run_config, output_file)
                if result:
                    all_results.append(result)
                
                # Check timeout between iterations
                abort_on_timeout()

    if all_results:
        # After grid is complete, run regression analysis on the collected results
        analyze_scaling_law(all_results, output_file)
        
        # Append all results to CSV
        append_results_to_csv(output_file, all_results)
        
        # Update state file
        update_state_main()

def main():
    parser = argparse.ArgumentParser(description="Nanomaterial Network Thermal Conductivity Simulation")
    parser.add_argument("--run-single", action="store_true", help="Run single simulation")
    parser.add_argument("--run-grid", action="store_true", help="Run simulation grid")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for single run")
    parser.add_argument("--N", type=int, default=100, help="Number of nodes")
    parser.add_argument("--target-degree", type=int, default=4, help="Target average degree")
    parser.add_argument("--material", type=str, default="Si", help="Material name")
    parser.add_argument("--output", type=str, default="data/processed/simulation_results.csv", help="Output CSV path")
    
    args = parser.parse_args()

    # Setup logging
    setup_logging()

    # Load base config from environment or defaults
    config = load_config()
    
    # Override with CLI args if provided
    if args.run_single:
        config.N = args.N
        config.target_degree = args.target_degree
        config.seed = args.seed
        config.material = args.material
        
        result = run_single_simulation(config, args.output)
        if result:
            append_results_to_csv(args.output, [result])
            update_state_main()
        else:
            logger.error("Single simulation failed.")
            sys.exit(1)
            
    elif args.run_grid:
        run_grid_simulation(config, args.output)
    else:
        parser.print_help()
        sys.exit(0)

if __name__ == "__main__":
    main()
