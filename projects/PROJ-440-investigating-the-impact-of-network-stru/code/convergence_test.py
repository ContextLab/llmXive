"""
Convergence Testing Logic for Driven Oscillator Simulations.

This module implements the generic algorithm to run simulations on multiple seeds
for a given graph topology to verify the stability and convergence of the decay
rate extraction. It does not depend on specific data files (parallel-safe logic),
but is designed to be called by the orchestration script (T024b) which provides
the graph data.
"""

import os
import sys
import json
import logging
import argparse
import hashlib
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from scipy.integrate import solve_ivp
import networkx as nx

# Import existing simulation utilities from the project API
from simulate_oscillators import (
    oscillator_equations,
    get_laplacian_matrix,
    compute_total_energy,
    extract_decay_rate,
    set_seed
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Simulation constants (matching T021/T022 specs)
SIMULATION_DURATION = 200.0
DRIVING_START = 0.0
DRIVING_END = 100.0
DAMPING_COEFFICIENT = 0.1
DRIVING_FREQUENCY = 1.0
NUM_SEEDS = 10  # Number of seeds for convergence testing

def run_convergence_simulation(
    graph: nx.Graph,
    base_seed: int,
    num_seeds: int = NUM_SEEDS
) -> List[Dict[str, Any]]:
    """
    Runs the oscillator simulation for a single graph across multiple random seeds.

    Args:
        graph: A NetworkX graph object representing the network topology.
        base_seed: The base integer seed for the first simulation.
        num_seeds: The total number of seeds to iterate through.

    Returns:
        A list of dictionaries, each containing the decay rate and fit quality
        for a specific seed.
    """
    results = []
    laplacian = get_laplacian_matrix(graph)
    n_nodes = graph.number_of_nodes()

    logger.info(f"Starting convergence test for graph with {n_nodes} nodes across {num_seeds} seeds.")

    for i in range(num_seeds):
        current_seed = base_seed + i
        set_seed(current_seed)

        # Initialize state: positions (x) and velocities (v)
        # x: random small displacement, v: zero initial velocity
        x0 = np.random.randn(n_nodes) * 0.1
        v0 = np.zeros(n_nodes)
        y0 = np.concatenate([x0, v0])

        # Define time points
        t_span = (0, SIMULATION_DURATION)
        t_eval = np.linspace(0, SIMULATION_DURATION, 2000)

        try:
            # Solve ODE
            sol = solve_ivp(
                oscillator_equations,
                t_span,
                y0,
                args=(laplacian, DAMPING_COEFFICIENT, DRIVING_FREQUENCY),
                method='DOP853',
                t_eval=t_eval,
                rtol=1e-9,
                atol=1e-12
            )

            if not sol.success:
                logger.warning(f"Seed {current_seed}: ODE solver failed to converge.")
                results.append({
                    'seed': current_seed,
                    'decay_rate': None,
                    'r_squared': None,
                    'status': 'failed',
                    'message': 'ODE convergence failure'
                })
                continue

            # Extract positions
            positions = sol.y[:n_nodes, :]
            energies = compute_total_energy(positions, sol.y[n_nodes:, :], laplacian)

            # Extract decay rate from post-transient phase (t > 100)
            # We need to map t_eval to indices
            transient_mask = t_eval > DRIVING_END
            t_transient = t_eval[transient_mask]
            e_transient = energies[transient_mask]

            if len(t_transient) < 10:
                logger.warning(f"Seed {current_seed}: Insufficient post-transient data.")
                results.append({
                    'seed': current_seed,
                    'decay_rate': None,
                    'r_squared': None,
                    'status': 'insufficient_data',
                    'message': 'Too few post-transient points'
                })
                continue

            decay_rate, r_squared, status, _ = extract_decay_rate(t_transient, e_transient)

            results.append({
                'seed': current_seed,
                'decay_rate': decay_rate,
                'r_squared': r_squared,
                'status': status
            })

        except Exception as e:
            logger.error(f"Seed {current_seed}: Unexpected error - {str(e)}")
            results.append({
                'seed': current_seed,
                'decay_rate': None,
                'r_squared': None,
                'status': 'error',
                'message': str(e)
            })

    return results

def compute_convergence_metrics(
    results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Computes statistical metrics to assess convergence across seeds.

    Args:
        results: List of result dictionaries from run_convergence_simulation.

    Returns:
        Dictionary containing mean decay rate, standard deviation, CV, and pass/fail status.
    """
    valid_decays = [r['decay_rate'] for r in results if r['decay_rate'] is not None]

    if len(valid_decays) < 2:
        return {
            'mean_decay_rate': None,
            'std_decay_rate': None,
            'coefficient_of_variation': None,
            'valid_count': len(valid_decays),
            'total_count': len(results),
            'converged': False,
            'reason': 'Insufficient valid results'
        }

    mean_val = np.mean(valid_decays)
    std_val = np.std(valid_decays)
    cv = std_val / mean_val if mean_val != 0 else float('inf')

    # Convergence criterion: std/mean < 0.01 (1%)
    is_converged = cv < 0.01

    return {
        'mean_decay_rate': float(mean_val),
        'std_decay_rate': float(std_val),
        'coefficient_of_variation': float(cv),
        'valid_count': len(valid_decays),
        'total_count': len(results),
        'converged': is_converged,
        'reason': 'Convergence threshold met' if is_converged else 'Convergence threshold not met (CV >= 0.01)'
    }

def plot_convergence_results(
    results: List[Dict[str, Any]],
    metrics: Dict[str, Any],
    output_path: str
) -> None:
    """
    Generates a plot visualizing the decay rates across different seeds.

    Args:
        results: List of result dictionaries.
        metrics: Computed convergence metrics.
        output_path: Path to save the plot (PNG).
    """
    import matplotlib.pyplot as plt

    seeds = [r['seed'] for r in results if r['decay_rate'] is not None]
    decays = [r['decay_rate'] for r in results if r['decay_rate'] is not None]

    plt.figure(figsize=(10, 6))
    plt.errorbar(seeds, decays, yerr=metrics.get('std_decay_rate', 0), fmt='o-', capsize=5)
    
    if metrics['mean_decay_rate'] is not None:
        plt.axhline(y=metrics['mean_decay_rate'], color='r', linestyle='--', label=f'Mean: {metrics["mean_decay_rate"]:.4f}')
    
    plt.title(f'Convergence Test: Decay Rate Variance Across Seeds\nCV={metrics.get("coefficient_of_variation", 0):.4f}')
    plt.xlabel('Random Seed')
    plt.ylabel('Decay Rate (λ)')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Convergence plot saved to {output_path}")

def main():
    """
    Entry point for the convergence testing script.
    
    This function is designed to be called by the T024b orchestration task.
    It expects graph data to be provided via arguments or a temporary file
    to ensure parallel safety (no direct file system dependency for input).
    """
    parser = argparse.ArgumentParser(description="Run convergence tests on a specific graph.")
    parser.add_argument('--graph-json', type=str, required=True, 
                        help='Path to a JSON file containing the graph edge list.')
    parser.add_argument('--base-seed', type=int, default=42, 
                        help='Base seed for the simulation.')
    parser.add_argument('--output-json', type=str, required=True,
                        help='Path to save the convergence results JSON.')
    parser.add_argument('--output-plot', type=str, required=True,
                        help='Path to save the convergence plot PNG.')
    
    args = parser.parse_args()

    # Load graph from JSON (edge list format)
    try:
        with open(args.graph_json, 'r') as f:
            graph_data = json.load(f)
        
        G = nx.Graph()
        G.add_edges_from(graph_data['edges'])
        logger.info(f"Loaded graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    except Exception as e:
        logger.error(f"Failed to load graph: {e}")
        sys.exit(1)

    # Run simulation
    results = run_convergence_simulation(G, args.base_seed)

    # Compute metrics
    metrics = compute_convergence_metrics(results)

    # Save results
    output_data = {
        'graph_info': {
            'nodes': G.number_of_nodes(),
            'edges': G.number_of_edges()
        },
        'simulation_params': {
            'base_seed': args.base_seed,
            'num_seeds': NUM_SEEDS,
            'damping': DAMPING_COEFFICIENT,
            'driving_freq': DRIVING_FREQUENCY
        },
        'metrics': metrics,
        'individual_results': results
    }

    os.makedirs(os.path.dirname(args.output_json), exist_ok=True)
    with open(args.output_json, 'w') as f:
        json.dump(output_data, f, indent=2)
    logger.info(f"Convergence results saved to {args.output_json}")

    # Generate plot
    plot_convergence_results(results, metrics, args.output_plot)

    # Exit with status based on convergence
    if not metrics['converged']:
        logger.warning(f"Convergence check FAILED: {metrics['reason']}")
        sys.exit(1)
    else:
        logger.info("Convergence check PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    main()
