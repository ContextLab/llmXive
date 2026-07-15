import os
import sys
import csv
import logging
import time
import argparse
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

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
from material_db import get_material_conductivity, list_available_materials
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
from utils import setup_logging, write_csv_row, format_error

# Global timer for runtime limit check
_start_time = None

def check_runtime_limit(config: SimulationConfig) -> bool:
    """Check if runtime limit has been exceeded. Returns True if OK, False if exceeded."""
    global _start_time
    if _start_time is None:
        _start_time = time.time()
        return True
    
    elapsed_hours = (time.time() - _start_time) / 3600.0
    if elapsed_hours > config.runtime_limit_hours:
        print("Runtime ceiling (6h) exceeded. Aborting grid.")
        sys.exit(1)
    return True

def load_existing_results(csv_path: str) -> List[Dict[str, Any]]:
    """Load existing results from CSV file."""
    results = []
    if os.path.exists(csv_path):
        try:
            with open(csv_path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Convert numeric fields
                    numeric_fields = ['N', 'p', 'avg_degree', 'conductivity', 
                                    'scaling_factor', 'percolation_threshold',
                                    'sensitivity_deviation', 'sensitivity_std', 'sensitivity_mean']
                    for field in numeric_fields:
                        if field in row and row[field]:
                            try:
                                row[field] = float(row[field])
                            except ValueError:
                                pass
                    results.append(row)
        except Exception as e:
            logging.warning(f"Could not load existing results: {e}")
    return results

def append_results_to_csv(csv_path: str, results: List[Dict[str, Any]]) -> None:
    """Append results to CSV file."""
    if not results:
        return
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(csv_path) if os.path.dirname(csv_path) else '.', exist_ok=True)
    
    # Check if file exists to determine if header is needed
    file_exists = os.path.exists(csv_path)
    
    with open(csv_path, 'a', newline='') as f:
        fieldnames = ['seed', 'N', 'p', 'avg_degree', 'conductivity', 
                     'percolation_flag', 'scaling_factor', 
                     'percolation_threshold', 'sensitivity_deviation', 
                     'sensitivity_std', 'sensitivity_mean']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        for result in results:
            # Ensure all fields are present
            row = {k: result.get(k, '') for k in fieldnames}
            writer.writerow(row)

def run_single_simulation(config: SimulationConfig) -> Optional[Dict[str, Any]]:
    """Run a single simulation with given parameters."""
    global _start_time
    if _start_time is None:
        _start_time = time.time()
    
    # Check runtime limit
    if not check_runtime_limit(config):
        return None
    
    try:
        # Get material conductivity
        bulk_k = get_material_conductivity(config.material, config.bulk_conductivity)
        
        # Generate network
        graph = generate_nanowire_network(
            N=config.N,
            p=config.p,
            seed=config.seed,
            target_degree=config.target_degree
        )
        
        # Calculate graph metrics
        avg_degree = calculate_average_degree(graph)
        avg_path = calculate_average_shortest_path_length(graph)
        clustering = calculate_clustering_coefficient(graph)
        
        # Check for percolation (largest component ratio)
        components = list(nx.connected_components(graph))
        largest_component_size = len(max(components, key=len))
        percolation_flag = largest_component_size / config.N >= 0.8
        
        if not percolation_flag and len(components) > 1:
            logging.warning("Graph disconnected; conductivity set to 0.0")
            conductivity = 0.0
        else:
            # Calculate thermal resistance
            edge_resistances = assign_thermal_resistance(
                graph, 
                bulk_k, 
                config.d, 
                config.l,
                config.lambda_phonon,
                config.specularity
            )
            
            # Solve Kirchhoff equations
            conductivity = solve_kirchhoff_heat_flow(
                graph, 
                edge_resistances,
                config.d,
                config.l
            )
        
        # Calculate scaling factor (relative to bulk)
        scaling_factor = conductivity / bulk_k if bulk_k > 0 else 0.0
        
        result = {
            'seed': config.seed,
            'N': config.N,
            'p': config.p,
            'avg_degree': avg_degree,
            'conductivity': conductivity,
            'percolation_flag': 1 if percolation_flag else 0,
            'scaling_factor': scaling_factor,
            'percolation_threshold': config.percolation_threshold or 0.0,
            'sensitivity_deviation': config.sensitivity_deviation or 0.0,
            'sensitivity_std': config.sensitivity_std or 0.0,
            'sensitivity_mean': config.sensitivity_mean or 0.0
        }
        
        logging.info(f"Simulation completed: N={config.N}, p={config.p}, "
                    f"avg_degree={avg_degree:.2f}, conductivity={conductivity:.2f}")
        
        return result
        
    except Exception as e:
        logging.error(f"Simulation failed: {format_error(e)}")
        return None

def run_grid_simulation(config: SimulationConfig) -> List[Dict[str, Any]]:
    """Run simulations over a grid of parameters."""
    results = []
    
    logging.info("Starting grid simulation")
    
    # Use grid parameters if defined, otherwise use single values
    N_values = config.grid_N_values if config.grid_N_values else [config.N]
    p_values = config.grid_p_values if config.grid_p_values else [config.p]
    
    for N in N_values:
        for p in p_values:
            # Create modified config for this iteration
            iter_config = SimulationConfig(
                N=N,
                p=p,
                d=config.d,
                l=config.l,
                seed=config.seed,
                material=config.material,
                bulk_conductivity=config.bulk_conductivity,
                lambda_phonon=config.lambda_phonon,
                specularity=config.specularity,
                runtime_limit_hours=config.runtime_limit_hours,
                target_degree=config.target_degree,
                output_csv=config.output_csv
            )
            
            result = run_single_simulation(iter_config)
            if result:
                results.append(result)
    
    return results

def run_sensitivity_analysis(config: SimulationConfig) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
    """Run sensitivity analysis on simulation results."""
    logging.info("Starting sensitivity analysis")
    
    # Run sensitivity sweep
    sweep_results = run_sensitivity_sweep(
        config=config,
        factor_range=config.sensitivity_factor_range
    )
    
    # Calculate deviation report
    deviation_report = calculate_deviation_report(sweep_results)
    
    # Analyze sensitivity
    sensitivity_metrics = analyze_sensitivity(deviation_report)
    
    # Update config with sensitivity results
    config.sensitivity_deviation = sensitivity_metrics.get('max_deviation', 0.0)
    config.sensitivity_std = sensitivity_metrics.get('std_dev', 0.0)
    config.sensitivity_mean = sensitivity_metrics.get('mean_deviation', 0.0)
    
    logging.info(f"Sensitivity analysis complete: "
                f"max_deviation={config.sensitivity_deviation:.4f}, "
                f"std_dev={config.sensitivity_std:.4f}")
    
    return sweep_results, sensitivity_metrics

def main():
    """Main entry point for the simulation pipeline."""
    global _start_time
    _start_time = time.time()
    
    # Setup logging
    setup_logging()
    logging.info("Starting thermal conductivity simulation pipeline")
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Nanowire network thermal conductivity simulation")
    parser.add_argument('--run-single', action='store_true', help='Run single simulation')
    parser.add_argument('--run-grid', action='store_true', help='Run grid simulation')
    parser.add_argument('--sensitivity-only', action='store_true', help='Run only sensitivity analysis')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--N', type=int, help='Number of nodes')
    parser.add_argument('--p', type=float, help='Connection probability')
    parser.add_argument('--target-degree', type=float, help='Target average degree')
    parser.add_argument('--material', type=str, help='Material name')
    parser.add_argument('--output', type=str, help='Output CSV path')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Override with command line arguments
    if args.seed:
        config.seed = args.seed
    if args.N:
        config.N = args.N
    if args.p:
        config.p = args.p
    if args.target_degree:
        config.target_degree = args.target_degree
    if args.material:
        config.material = args.material
    if args.output:
        config.output_csv = args.output
    
    # Load existing results
    existing_results = load_existing_results(config.output_csv)
    logging.info(f"Loaded {len(existing_results)} existing results")
    
    all_results = []
    
    try:
        if args.sensitivity_only:
            # Run only sensitivity analysis
            sensitivity_results, sensitivity_metrics = run_sensitivity_analysis(config)
            
            # Create result entries with sensitivity metrics
            for N in config.grid_N_values:
                for p in config.grid_p_values:
                    result = {
                        'seed': config.seed,
                        'N': N,
                        'p': p,
                        'avg_degree': 0.0,  # Will be computed
                        'conductivity': 0.0,  # Will be computed
                        'percolation_flag': 0,
                        'scaling_factor': 0.0,
                        'percolation_threshold': config.percolation_threshold or 0.0,
                        'sensitivity_deviation': config.sensitivity_deviation,
                        'sensitivity_std': config.sensitivity_std,
                        'sensitivity_mean': config.sensitivity_mean
                    }
                    all_results.append(result)
            
        elif args.run_single:
            # Run single simulation
            result = run_single_simulation(config)
            if result:
                all_results.append(result)
            
        elif args.run_grid:
            # Run grid simulation
            grid_results = run_grid_simulation(config)
            all_results.extend(grid_results)
            
            # Run regression analysis on grid results
            if len(grid_results) > 1:
                regression_results = run_ols_regression(grid_results)
                percolation_threshold = detect_percolation_threshold(grid_results)
                
                # Update config with percolation threshold
                config.percolation_threshold = percolation_threshold
                
                # Run sensitivity analysis on grid results
                if len(grid_results) >= 3:
                    sensitivity_results, sensitivity_metrics = run_sensitivity_analysis(config)
                    
                    # Update all results with sensitivity metrics
                    for result in all_results:
                        result['sensitivity_deviation'] = config.sensitivity_deviation
                        result['sensitivity_std'] = config.sensitivity_std
                        result['sensitivity_mean'] = config.sensitivity_mean
        else:
            # Default: run single simulation
            result = run_single_simulation(config)
            if result:
                all_results.append(result)
        
        # Append results to CSV
        if all_results:
            append_results_to_csv(config.output_csv, all_results)
            logging.info(f"Appended {len(all_results)} results to {config.output_csv}")
        
        # Log summary
        if all_results:
            avg_conductivity = sum(r['conductivity'] for r in all_results) / len(all_results)
            logging.info(f"Pipeline complete. Average conductivity: {avg_conductivity:.2f} W/(m·K)")
            
    except Exception as e:
        logging.error(f"Pipeline failed: {format_error(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
