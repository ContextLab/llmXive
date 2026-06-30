import os
import sys
import csv
import logging
import time
from typing import List, Dict, Any, Optional

import numpy as np
import networkx as nx
from scipy import sparse
from scipy.sparse.linalg import spsolve

from config import SimulationConfig, load_config, get_simulation_parameters
from generate_networks import generate_nanowire_network, generate_network_grid
from material_db import get_material_conductivity
from thermal_solver import (
    calculate_fuchs_sondheimer_factor,
    assign_thermal_resistance,
    build_edge_resistances,
    solve_kirchhoff_heat_flow,
    calculate_effective_conductivity,
)
from utils import setup_logging, write_csv_row

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

# Global timeout threshold: 6 hours in seconds
RUNTIME_TIMEOUT_SECONDS = 6 * 60 * 60
START_TIME = time.time()

def load_existing_results(filepath: str) -> List[Dict[str, Any]]:
    """Load existing results from CSV if it exists."""
    if not os.path.exists(filepath):
        return []
    results = []
    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results

def append_results_to_csv(filepath: str, results: List[Dict[str, Any]]) -> None:
    """Append results to the CSV file."""
    if not results:
        return
    fieldnames = [
        'seed', 'N', 'p', 'avg_degree', 'conductivity',
        'percolation_flag', 'scaling_factor'
    ]
    file_exists = os.path.exists(filepath)
    with open(filepath, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for row in results:
            writer.writerow(row)

def run_simulation(
    seed: int,
    N: int,
    p: float,
    target_degree: float,
    material: str,
    d: float,
    l: float,
    config: SimulationConfig
) -> Dict[str, Any]:
    """Run a single simulation iteration."""
    # Check global timer at the start of every simulation iteration
    elapsed = time.time() - START_TIME
    if elapsed > RUNTIME_TIMEOUT_SECONDS:
        logger.error("Runtime ceiling (6h) exceeded. Aborting grid.")
        sys.exit(1)

    try:
        # Generate network
        G = generate_nanowire_network(seed, N, p, target_degree)
        
        # Calculate average degree
        avg_degree = sum(dict(G.degree()).values()) / N if N > 0 else 0.0
        
        # Check connectivity
        is_connected = nx.is_connected(G) if G.number_of_nodes() > 1 else True
        percolation_flag = 1 if is_connected else 0

        if not is_connected:
            logger.warning("Graph disconnected; conductivity set to 0.0")
            conductivity = 0.0
        else:
            # Get material conductivity
            k_bulk = get_material_conductivity(material)
            
            # Calculate Fuchs-Sondheimer factor
            fs_factor = calculate_fuchs_sondheimer_factor(d, config.lambda_n, config.p_specular)
            
            # Assign thermal resistance
            edge_resistances = assign_thermal_resistance(G, k_bulk, d, l, fs_factor)
            
            # Solve Kirchhoff heat flow
            conductivity = solve_kirchhoff_heat_flow(G, edge_resistances)

        return {
            'seed': seed,
            'N': N,
            'p': p,
            'avg_degree': avg_degree,
            'conductivity': conductivity,
            'percolation_flag': percolation_flag,
            'scaling_factor': fs_factor
        }
    except Exception as e:
        logger.error(f"Simulation failed for seed={seed}, N={N}, p={p}: {e}")
        return {
            'seed': seed,
            'N': N,
            'p': p,
            'avg_degree': 0.0,
            'conductivity': 0.0,
            'percolation_flag': 0,
            'scaling_factor': 1.0
        }

def main():
    """Main entry point for the simulation pipeline."""
    # Load configuration
    config = load_config()
    params = get_simulation_parameters(config)
    
    # Output file path
    output_file = params.get('output_file', 'data/processed/simulation_results.csv')
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Load existing results
    existing_results = load_existing_results(output_file)
    logger.info(f"Loaded {len(existing_results)} existing results.")
    
    # Define simulation grid
    seeds = params.get('seeds', [42])
    N_values = params.get('N_values', [100])
    p_values = params.get('p_values', [0.1])
    target_degrees = params.get('target_degrees', [4.0])
    material = params.get('material', 'Si')
    d = params.get('d', 50.0)  # nm
    l = params.get('l', 1000.0)  # nm
    
    results_to_append = []
    
    # Run grid simulation
    for seed in seeds:
        for N in N_values:
            for p in p_values:
                for target_degree in target_degrees:
                    result = run_simulation(
                        seed=seed,
                        N=N,
                        p=p,
                        target_degree=target_degree,
                        material=material,
                        d=d,
                        l=l,
                        config=config
                    )
                    results_to_append.append(result)
    
    # Append results to CSV
    if results_to_append:
        append_results_to_csv(output_file, results_to_append)
        logger.info(f"Appended {len(results_to_append)} new results to {output_file}.")
    else:
        logger.info("No new results to append.")

if __name__ == '__main__':
    main()