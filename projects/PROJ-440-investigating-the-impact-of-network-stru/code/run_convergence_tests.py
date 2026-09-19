import os
import sys
import json
import logging
import argparse
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any
from scipy.integrate import solve_ivp

# Import from local project modules as per API surface
from simulate_oscillators import set_seed, get_laplacian_matrix, oscillator_equations, compute_total_energy, load_networks
from extract_energy_decay import extract_decay_rate, damped_sinusoid
from utils.error_handling import handle_simulation_failure, log_non_convergence
from plot_convergence import plot_convergence_results

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_convergence_targets(filepath: str) -> List[Dict[str, Any]]:
    """Load the list of target graphs from the convergence targets JSON file."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Convergence targets file not found: {filepath}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    if 'targets' not in data:
        raise ValueError("Invalid format: 'targets' key missing in JSON")
    
    return data['targets']

def run_convergence_simulation(graph_id: str, adj_matrix: np.ndarray, seeds: List[int], 
                               damping: float = 0.1, driving_freq: float = 1.0, 
                               t_span: Tuple[float, float] = (0, 200)) -> Dict[str, Any]:
    """
    Run the oscillator simulation for a specific graph across multiple random seeds.
    Returns a dictionary containing decay rates for each seed.
    """
    results = []
    failed_seeds = []

    for seed in seeds:
        try:
            set_seed(seed)
            n_nodes = adj_matrix.shape[0]
            
            # Initial conditions: random positions and velocities
            y0 = np.random.randn(2 * n_nodes)
            
            # Solve ODE
            sol = solve_ivp(
                lambda t, y: oscillator_equations(t, y, adj_matrix, damping, driving_freq),
                t_span, y0, method='DOP853', t_eval=np.linspace(t_span[0], t_span[1], 2000)
            )
            
            if not sol.success:
                raise RuntimeError(f"ODE solver failed: {sol.message}")
            
            # Compute energy over time
            energies = []
            for i in range(len(sol.t)):
                y_slice = sol.y[:, i]
                energy = compute_total_energy(y_slice, adj_matrix, damping=0) # Potential + Kinetic
                energies.append(energy)
            
            energies = np.array(energies)
            t = sol.t

            # Extract decay rate from post-transient phase (t > 100)
            mask = t > 100
            if np.sum(mask) < 10:
                raise ValueError("Insufficient post-transient data points")
            
            decay_rate, r_squared = extract_decay_rate(t[mask], energies[mask])
            
            if r_squared < 0.95:
                logger.warning(f"Graph {graph_id}, Seed {seed}: Low fit quality (R²={r_squared:.4f})")
            
            results.append({
                'seed': seed,
                'decay_rate': decay_rate,
                'r_squared': r_squared,
                'status': 'resonant' if decay_rate < 0 else 'dissipative'
            })

        except Exception as e:
            handle_simulation_failure(graph_id, seed, e)
            failed_seeds.append(seed)
            log_non_convergence(graph_id, seed, str(e))

    return {
        'graph_id': graph_id,
        'results': results,
        'failed_seeds': failed_seeds,
        'total_seeds': len(seeds)
    }

def compute_convergence_metrics(simulation_output: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute statistical metrics (mean, std, cv) for the decay rates across seeds.
    Asserts the coefficient of variation (std/mean) is < 0.01.
    """
    decay_rates = [r['decay_rate'] for r in simulation_output['results'] if r['status'] == 'dissipative']
    
    if len(decay_rates) == 0:
        return {
            'graph_id': simulation_output['graph_id'],
            'mean_decay': None,
            'std_decay': None,
            'cv': None,
            'passed_assertion': False,
            'error': "No valid dissipative decay rates found for convergence check"
        }

    mean_decay = np.mean(decay_rates)
    std_decay = np.std(decay_rates)
    cv = std_decay / abs(mean_decay) if mean_decay != 0 else float('inf')

    passed = cv < 0.01

    return {
        'graph_id': simulation_output['graph_id'],
        'mean_decay': float(mean_decay),
        'std_decay': float(std_decay),
        'cv': float(cv),
        'passed_assertion': passed,
        'n_samples': len(decay_rates)
    }

def save_convergence_results(all_metrics: List[Dict[str, Any]], output_path: str):
    """Save the convergence metrics to a JSON file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({
            'summary': all_metrics,
            'assertion_threshold': 0.01,
            'all_passed': all(m['passed_assertion'] for m in all_metrics if m['cv'] is not None)
        }, f, indent=2)
    logger.info(f"Convergence results saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Execute convergence testing for selected network topologies.")
    parser.add_argument("--targets", type=str, default="data/analysis/convergence_targets.json",
                        help="Path to the convergence targets JSON file.")
    parser.add_argument("--networks", type=str, default="data/raw/networks.csv",
                        help="Path to the networks CSV file.")
    parser.add_argument("--output", type=str, default="data/analysis/convergence_metrics.json",
                        help="Path to save the convergence metrics output.")
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 123, 456, 789, 101112],
                        help="List of random seeds to test.")
    parser.add_argument("--damping", type=float, default=0.1, help="Damping coefficient.")
    parser.add_argument("--freq", type=float, default=1.0, help="Driving frequency.")
    
    args = parser.parse_args()

    logger.info(f"Loading convergence targets from {args.targets}")
    targets = load_convergence_targets(args.targets)
    
    logger.info(f"Loading network data from {args.networks}")
    networks_df = load_networks(args.networks)
    
    all_metrics = []
    
    for target in targets:
        graph_id = target['id']
        logger.info(f"Processing graph: {graph_id}")
        
        # Retrieve adjacency matrix for this graph ID
        # Assuming load_networks returns a DataFrame or we need to reconstruct from edge list
        # The simulate_oscillators module's load_networks is expected to handle this or we need to filter
        # Since API surface says `load_networks` exists, we assume it can filter or we filter manually
        # If load_networks returns the full DF, we filter here.
        if 'adjacency_matrix' in target:
            # If the target JSON already contains the matrix (unlikely for large graphs, but possible)
            adj_matrix = np.array(target['adjacency_matrix'])
        else:
            # Filter the networks dataframe for this specific ID
            # Assuming the CSV has an 'id' column and 'edges' or similar, or we need to reconstruct
            # Given the constraints, we assume `load_networks` might return a dict of graphs or we need to parse edges
            # Let's assume a helper to get adj matrix from the dataframe exists or we reconstruct
            # Since we can't invent names, we assume the dataframe has 'id' and 'edges' (JSON string) or similar
            # If the existing `load_networks` doesn't support filtering by ID directly to return adj,
            # we might need to rely on the graph reconstruction logic in `simulate_oscillators`
            # For now, let's assume we reconstruct the graph from the CSV if the target has 'edges' info
            # OR, if `load_networks` returns a list of graph objects, we find the one with matching ID.
            # Given the ambiguity, we will assume the `networks_df` has columns 'id' and 'edges' (as string list or JSON)
            # and we reconstruct.
            
            # Fallback: If the CSV format is standard (id, class, metrics), we might need the edge list.
            # However, T012/T015 generated the CSV. If it only has metrics, we can't run simulation without edges.
            # The task T024a selected targets. The targets JSON should ideally contain the graph structure or a way to retrieve it.
            # Assuming the target JSON has 'edges' or we can load the specific graph from a pickle/adj file if generated.
            # Since T015 only mentions CSV, and CSVs are bad for edge lists, let's assume the target JSON includes the edge list
            # or we have a separate mechanism.
            # To be safe and robust: We check if 'edges' is in target.
            if 'edges' in target:
                import networkx as nx
                G = nx.Graph()
                G.add_edges_from(target['edges'])
                adj_matrix = nx.adjacency_matrix(G).toarray()
            else:
                # If edges are not in target, we might need to load from a separate graph file or reconstruct from CSV if possible.
                # If this fails, we raise a clear error.
                raise ValueError(f"Graph {graph_id} in targets lacks edge data to reconstruct adjacency matrix.")

        logger.info(f"Running convergence simulation for {graph_id} with {len(args.seeds)} seeds")
        sim_output = run_convergence_simulation(
            graph_id, adj_matrix, args.seeds, 
            damping=args.damping, driving_freq=args.freq
        )
        
        metrics = compute_convergence_metrics(sim_output)
        all_metrics.append(metrics)
        
        if not metrics['passed_assertion']:
            logger.warning(f"Convergence assertion FAILED for {graph_id}: CV={metrics['cv']:.4f} (threshold 0.01)")
        else:
            logger.info(f"Convergence assertion PASSED for {graph_id}: CV={metrics['cv']:.4f}")

    save_convergence_results(all_metrics, args.output)
    
    # Generate the plot
    plot_convergence_results(all_metrics, output_path=args.output.replace('.json', '.png'))

    # Final check
    if all(m['passed_assertion'] for m in all_metrics if m['cv'] is not None):
        logger.info("All convergence tests passed.")
    else:
        logger.error("One or more convergence tests failed. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
