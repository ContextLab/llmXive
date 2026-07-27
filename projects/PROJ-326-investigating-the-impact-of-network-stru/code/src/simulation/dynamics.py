"""
Dynamics module for spin system simulations.
Implements simplified Ising spin-flip dynamics, energy calculations, and conservation checks.
"""

import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import networkx as nx

from code.src.simulation.metrics import get_energy_profile, calculate_spatial_variance

logger = logging.getLogger(__name__)

class DynamicsError(Exception):
    """Custom exception for dynamics-related errors."""
    pass

def initialize_spins(graph: nx.Graph, seed: Optional[int] = None) -> np.ndarray:
    """
    Initialize spins on the graph nodes.
    
    Args:
        graph: NetworkX graph representing the spin network.
        seed: Random seed for reproducibility.
        
    Returns:
        numpy array of spin values (+1 or -1) for each node.
    """
    if seed is not None:
        np.random.seed(seed)
        
    n_nodes = graph.number_of_nodes()
    # Initialize spins randomly as +1 or -1
    spins = np.random.choice([-1, 1], size=n_nodes)
    logger.info(f"Initialized {n_nodes} spins with seed {seed}")
    return spins

def calculate_local_energy(graph: nx.Graph, spins: np.ndarray, j_coupling: float = 1.0) -> np.ndarray:
    """
    Calculate local energy contribution for each node.
    E_i = -J * sum_{j in neighbors(i)} s_i * s_j
    
    Args:
        graph: NetworkX graph representing the spin network.
        spins: Array of spin values.
        j_coupling: Coupling constant J.
        
    Returns:
        Array of local energies for each node.
    """
    n_nodes = graph.number_of_nodes()
    local_energies = np.zeros(n_nodes)
    
    for i, node in enumerate(graph.nodes()):
        neighbor_indices = list(graph.neighbors(node))
        if neighbor_indices:
            # Get spins of neighbors
            neighbor_spins = spins[neighbor_indices]
            # Calculate interaction energy
            local_energies[i] = -j_coupling * spins[i] * np.sum(neighbor_spins)
            
    return local_energies

def calculate_total_energy(graph: nx.Graph, spins: np.ndarray, j_coupling: float = 1.0) -> float:
    """
    Calculate total system energy.
    E = -J * sum_{(i,j) in edges} s_i * s_j
    
    Args:
        graph: NetworkX graph representing the spin network.
        spins: Array of spin values.
        j_coupling: Coupling constant J.
        
    Returns:
        Total system energy.
    """
    total_energy = 0.0
    for i, j in graph.edges():
        total_energy += -j_coupling * spins[i] * spins[j]
    return total_energy

def calculate_boltzmann_probability(delta_e: float, temperature: float, k_b: float = 1.0) -> float:
    """
    Calculate Boltzmann probability for a spin flip.
    P = exp(-delta_E / (k_B * T))
    
    Args:
        delta_e: Energy change from the proposed spin flip.
        temperature: Temperature T.
        k_b: Boltzmann constant (default 1.0 for reduced units).
        
    Returns:
        Boltzmann probability.
    """
    if temperature <= 0:
        return 0.0 if delta_e > 0 else 1.0
        
    exponent = -delta_e / (k_b * temperature)
    # Avoid overflow for large negative exponents
    if exponent < -700:
        return 0.0
    if exponent > 700:
        return 1.0
        
    return np.exp(exponent)

def attempt_spin_flip(graph: nx.Graph, spins: np.ndarray, node_idx: int, 
                     temperature: float, j_coupling: float = 1.0) -> Tuple[np.ndarray, float, bool]:
    """
    Attempt a spin flip at a specific node using Metropolis criterion.
    
    Args:
        graph: NetworkX graph representing the spin network.
        spins: Current spin configuration.
        node_idx: Index of the node to attempt flip on.
        temperature: Temperature T.
        j_coupling: Coupling constant J.
        
    Returns:
        Tuple of (new_spins, energy_change, flip_accepted)
    """
    current_spin = spins[node_idx]
    
    # Calculate current local energy
    current_local_energy = calculate_local_energy(graph, spins, j_coupling)[node_idx]
    
    # Calculate energy if spin were flipped
    test_spins = spins.copy()
    test_spins[node_idx] = -current_spin
    test_local_energy = calculate_local_energy(graph, test_spins, j_coupling)[node_idx]
    
    # Energy change: delta_E = E_new - E_old
    # Note: We only need local change since other nodes are unchanged
    delta_e = test_local_energy - current_local_energy
    
    # Metropolis criterion
    if delta_e <= 0:
        # Always accept if energy decreases or stays same
        new_spins = test_spins
        accepted = True
    else:
        # Accept with Boltzmann probability
        prob = calculate_boltzmann_probability(delta_e, temperature)
        accepted = np.random.random() < prob
        new_spins = test_spins if accepted else spins.copy()
        
    return new_spins, delta_e, accepted

def run_spin_flip_iteration(graph: nx.Graph, spins: np.ndarray, temperature: float,
                           j_coupling: float = 1.0, seed: Optional[int] = None) -> Tuple[np.ndarray, float, int]:
    """
    Run one iteration of spin-flip dynamics (one sweep through all nodes).
    
    Args:
        graph: NetworkX graph representing the spin network.
        spins: Current spin configuration.
        temperature: Temperature T.
        j_coupling: Coupling constant J.
        seed: Random seed for node selection order.
        
    Returns:
        Tuple of (new_spins, total_energy_change, n_accepted_flips)
    """
    if seed is not None:
        np.random.seed(seed)
        
    n_nodes = graph.number_of_nodes()
    current_spins = spins.copy()
    total_energy_change = 0.0
    n_accepted = 0
    
    # Randomize order of node updates
    node_indices = list(range(n_nodes))
    np.random.shuffle(node_indices)
    
    for node_idx in node_indices:
        new_spins, delta_e, accepted = attempt_spin_flip(
            graph, current_spins, node_idx, temperature, j_coupling
        )
        
        if accepted:
            current_spins = new_spins
            total_energy_change += delta_e
            n_accepted += 1
            
    return current_spins, total_energy_change, n_accepted

def run_simulation(graph: nx.Graph, n_steps: int, temperature: float, 
                 j_coupling: float = 1.0, seed: Optional[int] = None,
                 record_interval: int = 10) -> Dict[str, Any]:
    """
    Run the full spin-flip simulation for a specified number of steps.
    
    Args:
        graph: NetworkX graph representing the spin network.
        n_steps: Number of simulation steps (sweeps).
        temperature: Temperature T.
        j_coupling: Coupling constant J.
        seed: Random seed for reproducibility.
        record_interval: Interval at which to record metrics.
        
    Returns:
        Dictionary containing simulation results including energy profile,
        spatial variance, and acceptance rates.
    """
    if seed is not None:
        np.random.seed(seed)
        
    # Initialize spins
    spins = initialize_spins(graph, seed)
    
    # Initialize tracking variables
    energy_profile = []
    spatial_variance_profile = []
    acceptance_rates = []
    total_energy = calculate_total_energy(graph, spins, j_coupling)
    energy_profile.append(total_energy)
    
    logger.info(f"Starting simulation: {n_steps} steps, T={temperature}, J={j_coupling}")
    
    for step in range(n_steps):
        # Run one iteration
        spins, delta_e, n_accepted = run_spin_flip_iteration(
            graph, spins, temperature, j_coupling, seed=seed + step if seed else None
        )
        
        # Update total energy
        total_energy = calculate_total_energy(graph, spins, j_coupling)
        energy_profile.append(total_energy)
        
        # Calculate spatial variance
        spatial_var = calculate_spatial_variance(graph, spins)
        spatial_variance_profile.append(spatial_var)
        
        # Record acceptance rate
        acceptance_rate = n_accepted / graph.number_of_nodes()
        acceptance_rates.append(acceptance_rate)
        
        # Log progress at intervals
        if (step + 1) % record_interval == 0:
            logger.debug(f"Step {step+1}/{n_steps}: E={total_energy:.4f}, "
                       f"var={spatial_var:.4f}, acc_rate={acceptance_rate:.4f}")
    
    # Store final state
    results = {
        'spins': spins,
        'energy_profile': energy_profile,
        'spatial_variance_profile': spatial_variance_profile,
        'acceptance_rates': acceptance_rates,
        'n_steps': n_steps,
        'temperature': temperature,
        'j_coupling': j_coupling,
        'seed': seed,
        'final_energy': total_energy,
        'final_spatial_variance': spatial_variance_profile[-1] if spatial_variance_profile else 0.0
    }
    
    logger.info(f"Simulation completed: final E={total_energy:.4f}, "
               f"final var={results['final_spatial_variance']:.4f}")
    
    return results

def check_energy_conservation(energy_profile: List[float], tolerance: float = 1e-6) -> Dict[str, Any]:
    """
    Check energy conservation in the simulation profile.
    For a closed system with no external work, total energy should be conserved
    (allowing for small numerical fluctuations in the Metropolis algorithm).
    Note: In the Metropolis algorithm, energy is NOT strictly conserved due to
    thermal fluctuations, so we check that the energy changes are within
    expected thermal fluctuations rather than strict conservation.
    
    Args:
        energy_profile: List of energy values over time steps.
        tolerance: Maximum allowed relative change per step.
        
    Returns:
        Dictionary with conservation check results.
    """
    if len(energy_profile) < 2:
        return {
            'conserved': True,
            'max_relative_change': 0.0,
            'mean_relative_change': 0.0,
            'message': 'Insufficient data points for conservation check'
        }
    
    energy_array = np.array(energy_profile)
    relative_changes = np.abs(np.diff(energy_array) / (energy_array[:-1] + 1e-10))
    
    max_relative_change = np.max(relative_changes)
    mean_relative_change = np.mean(relative_changes)
    
    # Check if changes are within tolerance
    # Note: For Metropolis at finite temperature, we expect some energy fluctuation
    # The tolerance here is for detecting numerical instability, not strict conservation
    is_conserved = max_relative_change < tolerance
    
    result = {
        'conserved': is_conserved,
        'max_relative_change': float(max_relative_change),
        'mean_relative_change': float(mean_relative_change),
        'tolerance': tolerance,
        'n_steps': len(energy_profile),
        'initial_energy': float(energy_profile[0]),
        'final_energy': float(energy_profile[-1]),
        'total_energy_change': float(energy_profile[-1] - energy_profile[0])
    }
    
    if not is_conserved:
        result['message'] = f"Energy change exceeds tolerance: max_rel_change={max_relative_change:.2e} > {tolerance:.2e}"
    else:
        result['message'] = "Energy conservation check passed within tolerance"
        
    return result

def validate_simulation_results(simulation_results: Dict[str, Any], 
                               energy_tolerance: float = 1e-6,
                               variance_monotonicity_tolerance: float = 0.1) -> Dict[str, Any]:
    """
    Validate simulation results including energy conservation and other checks.
    
    Args:
        simulation_results: Dictionary containing simulation results.
        energy_tolerance: Tolerance for energy conservation check.
        variance_monotonicity_tolerance: Tolerance for spatial variance monotonicity check.
        
    Returns:
        Dictionary with validation results.
    """
    validation = {
        'valid': True,
        'checks': {},
        'warnings': [],
        'errors': []
    }
    
    # Check energy conservation
    if 'energy_profile' in simulation_results:
        energy_check = check_energy_conservation(
            simulation_results['energy_profile'], 
            energy_tolerance
        )
        validation['checks']['energy_conservation'] = energy_check
        if not energy_check['conserved']:
            validation['warnings'].append(energy_check['message'])
            # Note: Not marking as invalid since Metropolis allows fluctuations
    else:
        validation['errors'].append("Missing energy_profile in simulation results")
        validation['valid'] = False
        
    # Check spatial variance monotonicity (should generally increase or stay stable)
    if 'spatial_variance_profile' in simulation_results:
        var_profile = simulation_results['spatial_variance_profile']
        if len(var_profile) >= 2:
            decreases = 0
            total_steps = len(var_profile) - 1
            for i in range(1, len(var_profile)):
                if var_profile[i] < var_profile[i-1] - variance_monotonicity_tolerance:
                    decreases += 1
            
            if decreases > 0:
                validation['checks']['variance_monotonicity'] = {
                    'monotonic': False,
                    'decreases': decreases,
                    'total_steps': total_steps,
                    'decrease_ratio': decreases / total_steps
                }
                validation['warnings'].append(
                    f"Spatial variance decreased {decreases}/{total_steps} times"
                )
            else:
                validation['checks']['variance_monotonicity'] = {
                    'monotonic': True,
                    'message': 'Spatial variance increased or remained stable throughout'
                }
    else:
        validation['warnings'].append("Missing spatial_variance_profile in simulation results")
        
    # Check acceptance rates are reasonable
    if 'acceptance_rates' in simulation_results:
        acc_rates = simulation_results['acceptance_rates']
        mean_acc = np.mean(acc_rates)
        if mean_acc < 0.01:
            validation['warnings'].append(f"Very low acceptance rate: {mean_acc:.4f}")
        elif mean_acc > 0.99:
            validation['warnings'].append(f"Very high acceptance rate: {mean_acc:.4f}")
            
    return validation

def main():
    """
    Main function to demonstrate the dynamics module.
    Creates a sample graph, runs simulation, and validates results.
    """
    import argparse
    from pathlib import Path
    import json
    
    parser = argparse.ArgumentParser(description='Run spin dynamics simulation')
    parser.add_argument('--graph', type=str, default='random', 
                      help='Type of graph: random, er, sw, sf')
    parser.add_argument('--n-nodes', type=int, default=50, help='Number of nodes')
    parser.add_argument('--n-steps', type=int, default=100, help='Number of simulation steps')
    parser.add_argument('--temperature', type=float, default=1.0, help='Temperature T')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--output', type=str, default='data/analysis/dynamics_test.json',
                      help='Output file path')
    args = parser.parse_args()
    
    # Create a sample graph
    import networkx as nx
    if args.graph == 'er':
        graph = nx.erdos_renyi_graph(args.n_nodes, 0.1, seed=args.seed)
    elif args.graph == 'sw':
        graph = nx.watts_strogatz_graph(args.n_nodes, 4, 0.1, seed=args.seed)
    elif args.graph == 'sf':
        graph = nx.barabasi_albert_graph(args.n_nodes, 2, seed=args.seed)
    else:
        graph = nx.erdos_renyi_graph(args.n_nodes, 0.1, seed=args.seed)
        
    # Ensure graph is connected
    if not nx.is_connected(graph):
        components = list(nx.connected_components(graph))
        largest_component = max(components, key=len)
        graph = graph.subgraph(largest_component).copy()
        logger.info(f"Graph disconnected, using largest component with {graph.number_of_nodes()} nodes")
    
    # Run simulation
    results = run_simulation(
        graph, 
        n_steps=args.n_steps,
        temperature=args.temperature,
        j_coupling=1.0,
        seed=args.seed,
        record_interval=10
    )
    
    # Validate results
    validation = validate_simulation_results(results)
    
    # Prepare output
    output = {
        'graph_info': {
            'n_nodes': graph.number_of_nodes(),
            'n_edges': graph.number_of_edges(),
            'is_connected': nx.is_connected(graph)
        },
        'simulation_params': {
            'n_steps': args.n_steps,
            'temperature': args.temperature,
            'j_coupling': 1.0,
            'seed': args.seed
        },
        'results': {
            'final_energy': results['final_energy'],
            'final_spatial_variance': results['final_spatial_variance'],
            'mean_acceptance_rate': float(np.mean(results['acceptance_rates'])),
            'n_accepted_flips': sum(1 for r in results['acceptance_rates'] if r > 0.5)
        },
        'validation': validation,
        'energy_conservation_check': check_energy_conservation(
            results['energy_profile'], 
            tolerance=1e-4  # Relaxed tolerance for Metropolis
        )
    }
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write output
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
        
    logger.info(f"Results written to {args.output}")
    return output

if __name__ == '__main__':
    main()