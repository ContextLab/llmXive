import os
import sys
import csv
import logging
import time
import argparse
from typing import List, Dict, Any, Optional

from config import SimulationConfig, load_config, get_simulation_parameters
from generate_networks import (
    generate_nanowire_network,
    calculate_average_degree,
    calculate_average_shortest_path_length,
    calculate_clustering_coefficient,
    generate_network_grid
)
from thermal_solver import (
    calculate_fuchs_sondheimer_factor,
    assign_thermal_resistance,
    build_edge_resistances,
    solve_kirchhoff_heat_flow,
    calculate_effective_conductivity
)
from material_db import get_material_conductivity
from regression_analysis import (
    run_ols_regression,
    calculate_correlation_matrix,
    detect_percolation_threshold,
    update_csv_with_percolation_threshold
)
from sensitivity_analysis import (
    run_sensitivity_sweep,
    calculate_deviation_report,
    report_sensitivity_results
)
from utils import setup_logging, write_csv_row, format_error

logger = logging.getLogger(__name__)

# Global start time for timeout check
START_TIME = time.time()

def check_runtime_limit(max_hours: float = 6.0) -> bool:
    """Check if runtime limit is exceeded."""
    elapsed = time.time() - START_TIME
    limit_seconds = max_hours * 3600
    return elapsed < limit_seconds

def abort_on_timeout(max_hours: float = 6.0) -> None:
    """Abort execution if runtime limit is exceeded."""
    if not check_runtime_limit(max_hours):
        logger.error("Runtime ceiling (6h) exceeded. Aborting grid.")
        sys.exit(1)

def load_existing_results(filepath: str) -> List[Dict[str, Any]]:
    """Load existing results from CSV if it exists."""
    results = []
    if os.path.exists(filepath):
        with open(filepath, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric fields
                for key in ['N', 'avg_degree', 'conductivity', 'percolation_flag', 'scaling_factor']:
                    if key in row and row[key]:
                        try:
                            row[key] = float(row[key])
                        except ValueError:
                            pass
                results.append(row)
    return results

def append_results_to_csv(filepath: str, row: Dict[str, Any]) -> None:
    """Append a single result row to the CSV file."""
    fieldnames = ['seed', 'N', 'p', 'avg_degree', 'conductivity', 'percolation_flag', 'scaling_factor', 
                  'sensitivity_min', 'sensitivity_max', 'sensitivity_deviation']
    
    file_exists = os.path.exists(filepath)
    
    with open(filepath, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

def run_single_simulation(config: SimulationConfig) -> Dict[str, Any]:
    """Run a single simulation for given config parameters."""
    seed = config.seed
    N = config.N
    p = config.p
    target_degree = config.target_degree
    material = config.material
    bulk_k = config.bulk_conductivity
    wire_diameter = config.diameter
    
    # Generate network
    if target_degree > 0:
        G = generate_nanowire_network_for_degree(N, target_degree, seed)
    else:
        G = generate_nanowire_network(N, p, seed)
        
    avg_degree = calculate_average_degree(G)
    is_connected = nx.is_connected(G)
    
    if not is_connected:
        logger.warning("Graph disconnected; conductivity set to 0.0")
        conductivity = 0.0
        percolation_flag = 0
    else:
        # Assign thermal resistances
        bulk_k_actual = get_material_conductivity(material, bulk_k)
        fs_factor = calculate_fuchs_sondheimer_factor(wire_diameter, bulk_k_actual)
        edge_resistances = build_edge_resistances(G, bulk_k_actual, fs_factor, wire_diameter)
        
        # Solve heat flow
        conductivity = solve_kirchhoff_heat_flow(G, edge_resistances)
        percolation_flag = 1
        
    result = {
        "seed": seed,
        "N": N,
        "p": p,
        "avg_degree": avg_degree,
        "conductivity": conductivity,
        "percolation_flag": percolation_flag,
        "scaling_factor": fs_factor,
        "sensitivity_min": None,
        "sensitivity_max": None,
        "sensitivity_deviation": None
    }
    
    return result

def run_grid_simulation(config: SimulationConfig, output_path: str) -> None:
    """Run simulations over a grid of parameters."""
    N_values = config.N_values
    p_values = config.p_values
    degree_values = config.degree_values
    seeds = config.seeds
    
    grid_results = generate_network_grid(N_values, p_values, degree_values, seeds)
    
    for item in grid_results:
        # Check timeout before each simulation
        abort_on_timeout()
        
        sim_config = SimulationConfig(
            seed=int(item['seed']),
            N=int(item['N']),
            p=float(item['p']),
            target_degree=int(item['target_degree']),
            material=config.material,
            bulk_conductivity=config.bulk_conductivity,
            diameter=config.diameter
        )
        
        result = run_single_simulation(sim_config)
        append_results_to_csv(output_path, result)
        logger.info(f"Completed simulation: seed={result['seed']}, N={result['N']}, cond={result['conductivity']:.4f}")

def run_regression_analysis(csv_path: str) -> None:
    """Run regression analysis on the simulation results."""
    if not os.path.exists(csv_path):
        logger.warning(f"No results file found at {csv_path}. Skipping regression.")
        return
        
    update_csv_with_percolation_threshold(csv_path)
    logger.info("Regression analysis completed and CSV updated.")

def run_sensitivity_analysis(csv_path: str, config: SimulationConfig) -> None:
    """Run sensitivity analysis and update CSV with metrics."""
    if not os.path.exists(csv_path):
        logger.warning(f"No results file found at {csv_path}. Skipping sensitivity analysis.")
        return
        
    # Run sensitivity sweep on the existing results
    sensitivity_results = run_sensitivity_sweep(csv_path, config)
    
    # Calculate deviation report
    deviation_report = calculate_deviation_report(sensitivity_results)
    
    # Update the CSV with sensitivity metrics
    report_sensitivity_results(csv_path, sensitivity_results, deviation_report)
    logger.info("Sensitivity analysis completed and CSV updated.")

def main():
    parser = argparse.ArgumentParser(description="Nanomaterial Thermal Conductivity Simulation")
    parser.add_argument('--run-single', action='store_true', help="Run a single simulation")
    parser.add_argument('--run-grid', action='store_true', help="Run grid simulation")
    parser.add_argument('--sensitivity-only', action='store_true', help="Run only sensitivity analysis")
    parser.add_argument('--seed', type=int, default=42, help="Random seed for single simulation")
    parser.add_argument('--output', type=str, default='data/processed/simulation_results.csv', help="Output CSV path")
    
    args = parser.parse_args()
    
    setup_logging()
    config = load_config()
    
    if args.run_single:
        config.seed = args.seed
        result = run_single_simulation(config)
        append_results_to_csv(args.output, result)
        logger.info(f"Single simulation complete. Result: {result}")
        
    elif args.run_grid:
        run_grid_simulation(config, args.output)
        run_regression_analysis(args.output)
        logger.info("Grid simulation complete.")
        
    elif args.sensitivity_only:
        run_sensitivity_analysis(args.output, config)
        
    else:
        # Default: run grid if no args provided
        if os.path.exists(args.output) and os.path.getsize(args.output) > 0:
            logger.info("Resuming with sensitivity analysis on existing data.")
            run_sensitivity_analysis(args.output, config)
        else:
            run_grid_simulation(config, args.output)
            run_regression_analysis(args.output)
            run_sensitivity_analysis(args.output, config)

if __name__ == "__main__":
    main()
