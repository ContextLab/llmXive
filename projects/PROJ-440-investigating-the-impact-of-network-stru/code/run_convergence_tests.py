"""
Execute convergence testing for selected network topologies.

This script runs simulations with multiple random seeds for each graph ID
in the convergence targets list, calculates the standard deviation of decay
rates, and verifies that the relative standard deviation (std/mean) is less
  than 0.01 as required by Spec SC-006.

Dependencies:
    - T024a: data/analysis/convergence_targets.json
    - T023a: Convergence testing algorithm logic
    - code/simulate_oscillators.py (for simulation logic)
"""
import os
import sys
import json
import logging
import argparse
import numpy as np
from pathlib import Path
from typing import Dict, List, Any

# Import simulation logic from existing module
from code.simulate_oscillators import simulate_graph, extract_decay_rate, load_networks
from code.utils.error_handling import handle_simulation_failure, log_non_convergence

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('state/convergence_test.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_SEEDS = list(range(10))  # 10 seeds for convergence testing
DEFAULT_DRIVING_FREQ = 1.0
DEFAULT_DAMPING = 0.1
DEFAULT_DURATION = 200.0
DEFAULT_TRANSIENT = 100.0
CONVERGENCE_THRESHOLD = 0.01  # SC-006: std/mean < 0.01

def load_convergence_targets(filepath: str) -> List[Dict[str, Any]]:
    """Load the list of target graph IDs from JSON."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Convergence targets file not found: {filepath}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    if 'targets' not in data:
        raise ValueError("Invalid format: 'targets' key missing in convergence targets file")
    
    return data['targets']

def run_convergence_simulation(
    graph_id: str,
    graph_data: Dict[str, Any],
    seeds: List[int],
    damping: float,
    driving_freq: float,
    duration: float,
    transient: float
) -> Dict[str, Any]:
    """
    Run simulation for a single graph with multiple seeds.
    
    Returns a dictionary containing:
        - graph_id: The ID of the graph
        - class: The topological class
        - decay_rates: List of decay rates from each seed
        - mean_decay: Mean decay rate
        - std_decay: Standard deviation of decay rates
        - relative_std: std/mean ratio
        - converged: Boolean indicating if relative_std < threshold
        - status: 'converged' or 'failed'
    """
    logger.info(f"Running convergence test for graph {graph_id} ({graph_data.get('class', 'unknown')}) with {len(seeds)} seeds")
    
    decay_rates = []
    failed_seeds = []
    
    for seed in seeds:
        try:
            # Simulate the graph with the given seed
            # We need to reconstruct the graph or use the adjacency matrix
            # Assuming graph_data contains necessary info to reconstruct
            adj_matrix = graph_data.get('adj_matrix')
            if adj_matrix is None:
                # If adj_matrix not stored, we might need to regenerate or load
                # For now, assume it's in the data or we use a placeholder
                # In a real implementation, we'd load the graph from file
                logger.warning(f"Adjacency matrix not found for {graph_id}, skipping")
                continue
            
            # Convert adj_matrix from list to numpy array if needed
            if isinstance(adj_matrix, list):
                adj_matrix = np.array(adj_matrix)
            
            # Run simulation
            result = simulate_graph(
                adj_matrix=adj_matrix,
                damping=damping,
                driving_freq=driving_freq,
                duration=duration,
                seed=seed
            )
            
            # Extract decay rate
            decay_rate = extract_decay_rate(result['energy'], transient=transient)
            decay_rates.append(decay_rate)
            logger.debug(f"  Seed {seed}: decay_rate = {decay_rate:.6f}")
            
        except Exception as e:
            logger.error(f"  Seed {seed} failed for graph {graph_id}: {str(e)}")
            failed_seeds.append(seed)
            # Continue with other seeds

    if len(decay_rates) == 0:
        logger.error(f"All seeds failed for graph {graph_id}")
        return {
            'graph_id': graph_id,
            'class': graph_data.get('class', 'unknown'),
            'decay_rates': [],
            'mean_decay': None,
            'std_decay': None,
            'relative_std': None,
            'converged': False,
            'status': 'failed',
            'failed_seeds': failed_seeds
        }
    
    # Calculate statistics
    decay_rates_array = np.array(decay_rates)
    mean_decay = np.mean(decay_rates_array)
    std_decay = np.std(decay_rates_array)
    relative_std = std_decay / mean_decay if mean_decay != 0 else float('inf')
    converged = relative_std < CONVERGENCE_THRESHOLD
    
    logger.info(f"  Results for {graph_id}: mean={mean_decay:.6f}, std={std_decay:.6f}, rel_std={relative_std:.4f}, converged={converged}")
    
    return {
        'graph_id': graph_id,
        'class': graph_data.get('class', 'unknown'),
        'decay_rates': decay_rates,
        'mean_decay': float(mean_decay),
        'std_decay': float(std_decay),
        'relative_std': float(relative_std),
        'converged': converged,
        'status': 'converged' if converged else 'failed',
        'failed_seeds': failed_seeds
    }

def compute_convergence_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute aggregate convergence metrics across all tested graphs.
    
    Returns:
        Dictionary with overall statistics and pass/fail status.
    """
    total_graphs = len(results)
    converged_graphs = sum(1 for r in results if r['converged'])
    failed_graphs = total_graphs - converged_graphs
    
    overall_status = 'passed' if failed_graphs == 0 else 'failed'
    
    return {
        'total_graphs_tested': total_graphs,
        'converged_graphs': converged_graphs,
        'failed_graphs': failed_graphs,
        'convergence_rate': converged_graphs / total_graphs if total_graphs > 0 else 0,
        'overall_status': overall_status,
        'threshold_used': CONVERGENCE_THRESHOLD
    }

def save_convergence_results(results: List[Dict[str, Any]], metrics: Dict[str, Any], output_path: str):
    """Save convergence test results to JSON file."""
    output_data = {
        'results': results,
        'metrics': metrics,
        'threshold': CONVERGENCE_THRESHOLD
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Convergence results saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Run convergence tests on selected network topologies')
    parser.add_argument('--targets', type=str, default='data/analysis/convergence_targets.json',
                      help='Path to convergence targets JSON file')
    parser.add_argument('--seeds', type=str, default=None,
                      help='Comma-separated list of random seeds (default: 0-9)')
    parser.add_argument('--damping', type=float, default=DEFAULT_DAMPING,
                      help='Damping coefficient (default: 0.1)')
    parser.add_argument('--driving-freq', type=float, default=DEFAULT_DRIVING_FREQ,
                      help='Driving frequency (default: 1.0)')
    parser.add_argument('--duration', type=float, default=DEFAULT_DURATION,
                      help='Simulation duration (default: 200.0)')
    parser.add_argument('--transient', type=float, default=DEFAULT_TRANSIENT,
                      help='Transient period to exclude (default: 100.0)')
    parser.add_argument('--output', type=str, default='data/analysis/convergence_results.json',
                      help='Output path for convergence results')
    
    args = parser.parse_args()
    
    # Parse seeds if provided
    if args.seeds:
        seeds = [int(s) for s in args.seeds.split(',')]
    else:
        seeds = DEFAULT_SEEDS
    
    logger.info(f"Starting convergence testing with {len(seeds)} seeds")
    logger.info(f"Targets file: {args.targets}")
    logger.info(f"Output file: {args.output}")
    
    # Load convergence targets
    try:
        targets = load_convergence_targets(args.targets)
        logger.info(f"Loaded {len(targets)} convergence targets")
    except Exception as e:
        logger.error(f"Failed to load convergence targets: {str(e)}")
        sys.exit(1)
    
    # Run convergence tests for each target
    results = []
    for target in targets:
        graph_id = target['graph_id']
        graph_data = target
        
        result = run_convergence_simulation(
            graph_id=graph_id,
            graph_data=graph_data,
            seeds=seeds,
            damping=args.damping,
            driving_freq=args.driving_freq,
            duration=args.duration,
            transient=args.transient
        )
        results.append(result)
    
    # Compute aggregate metrics
    metrics = compute_convergence_metrics(results)
    
    # Save results
    save_convergence_results(results, metrics, args.output)
    
    # Print summary
    print("\n" + "="*60)
    print("CONVERGENCE TEST SUMMARY")
    print("="*60)
    print(f"Total graphs tested: {metrics['total_graphs_tested']}")
    print(f"Converged: {metrics['converged_graphs']}")
    print(f"Failed: {metrics['failed_graphs']}")
    print(f"Convergence rate: {metrics['convergence_rate']:.2%}")
    print(f"Threshold: {metrics['threshold_used']}")
    print(f"Overall status: {metrics['overall_status'].upper()}")
    print("="*60)
    
    # Exit with error code if convergence failed
    if metrics['overall_status'] == 'failed':
        sys.exit(1)
    
    sys.exit(0)

if __name__ == '__main__':
    main()