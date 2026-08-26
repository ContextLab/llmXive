import os
import sys
import json
import hashlib
import logging
import argparse
import numpy as np
import pandas as pd
import networkx as nx
from scipy.integrate import solve_ivp
from scipy.optimize import curve_fit
from scipy.stats import linregress
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/simulation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def set_seed(seed):
    """Set random seed for reproducibility."""
    np.random.seed(seed)
    return seed

def get_laplacian_matrix(graph):
    """Compute the Laplacian matrix of a graph."""
    return nx.laplacian_matrix(graph).toarray()

def oscillator_equations(t, y, L, damping, driving_freq, driving_amp):
    """
    Equations of motion for driven damped oscillators.
    y: [x1, x2, ..., xn, vx1, vx2, ..., vxn]
    """
    n = len(y) // 2
    x = y[:n]
    v = y[n:]

    # Spring forces: -L @ x
    spring_force = -L @ x

    # Damping forces: -damping * v
    damping_force = -damping * v

    # Driving force: applied to a single node (node 0)
    drive = np.zeros(n)
    drive[0] = driving_amp * np.sin(driving_freq * t)

    # Total acceleration
    a = spring_force + damping_force + drive

    return np.concatenate([v, a])

def compute_total_energy(y, L, mass=1.0):
    """Compute total energy of the system."""
    n = len(y) // 2
    x = y[:n]
    v = y[n:]

    # Kinetic energy: 0.5 * m * v^2
    kinetic = 0.5 * mass * np.sum(v**2)

    # Potential energy: 0.5 * x^T @ L @ x
    potential = 0.5 * np.dot(x, L @ x)

    return kinetic + potential

def damped_sinusoid(t, A, lambda_decay, omega, phi, C):
    """Damped sinusoid model for energy decay."""
    return A * np.exp(-lambda_decay * t) * np.cos(omega * t + phi) + C

def extract_decay_rate(time_data, energy_data, t_start=100):
    """
    Extract decay rate from energy data by fitting a damped sinusoid.
    Returns (decay_rate, r_squared, status)
    """
    # Filter for post-transient phase
    mask = time_data >= t_start
    t_fit = time_data[mask]
    E_fit = energy_data[mask]

    if len(t_fit) < 10:
        logger.warning("Insufficient data points for fitting.")
        return None, 0.0, "non-convergent"

    # Initial parameter guesses
    A_init = E_fit[0]
    lambda_init = 0.01
    omega_init = 1.0
    phi_init = 0.0
    C_init = 0.0

    try:
        # Fit the model
        popt, pcov = curve_fit(
            damped_sinusoid, t_fit, E_fit,
            p0=[A_init, lambda_init, omega_init, phi_init, C_init],
            maxfev=10000
        )

        # Calculate R-squared
        E_pred = damped_sinusoid(t_fit, *popt)
        ss_res = np.sum((E_fit - E_pred)**2)
        ss_tot = np.sum((E_fit - np.mean(E_fit))**2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        decay_rate = popt[1]

        # Check for convergence issues
        if np.isnan(decay_rate) or np.isinf(decay_rate) or r_squared < 0.95:
            logger.warning(f"Fit quality insufficient: R²={r_squared:.4f}")
            return None, r_squared, "non-convergent"

        # Check for resonance (negative decay rate)
        if decay_rate < 0:
            return decay_rate, r_squared, "resonant"

        return decay_rate, r_squared, "dissipative"

    except Exception as e:
        logger.warning(f"Fitting failed: {str(e)}")
        return None, 0.0, "non-convergent"

def simulate_graph(graph_data, damping=0.1, driving_freq=1.0, driving_amp=1.0, seed=42):
    """
    Simulate oscillator dynamics on a single graph.
    Returns simulation results dictionary.
    """
    set_seed(seed)

    # Extract graph
    adj_matrix = np.array(graph_data['adj_matrix'])
    n_nodes = adj_matrix.shape[0]

    # Create graph object
    G = nx.from_numpy_array(adj_matrix)

    # Laplacian matrix
    L = get_laplacian_matrix(G)

    # Initial conditions: all positions 0, velocities 0
    y0 = np.zeros(2 * n_nodes)
    y0[n_nodes] = 1.0  # Initial velocity on node 0

    # Time span
    t_span = (0, 200)
    t_eval = np.linspace(0, 200, 2000)

    # Solve ODE
    try:
        sol = solve_ivp(
            oscillator_equations, t_span, y0,
            args=(L, damping, driving_freq, driving_amp),
            t_eval=t_eval, method='DOP853', rtol=1e-8, atol=1e-8
        )

        if not sol.success:
            logger.error(f"Integration failed: {sol.message}")
            return None

        # Compute energy at each time step
        energies = [compute_total_energy(y, L) for y in sol.y.T]
        energies = np.array(energies)

        # Extract decay rate
        decay_rate, r_squared, status = extract_decay_rate(t_eval, energies)

        if decay_rate is None:
            logger.error(f"Non-convergence detected for graph {graph_data['id']}")
            return None

        return {
            'graph_id': graph_data['id'],
            'decay_rate': decay_rate,
            'r_squared': r_squared,
            'status': status,
            'n_nodes': n_nodes,
            'seed': seed
        }

    except Exception as e:
        logger.error(f"Simulation failed for graph {graph_data['id']}: {str(e)}")
        return None

def load_networks(filepath):
    """Load networks from CSV file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Network file not found: {filepath}")

    df = pd.read_csv(filepath)
    networks = []

    for _, row in df.iterrows():
        # Reconstruct adjacency matrix from edge list string
        edges_str = row['edges']
        edges = []
        if edges_str and edges_str != '[]':
            edges_str = edges_str.strip('[]').replace(' ', '')
            if edges_str:
                edge_pairs = edges_str.split('),(')
                for pair in edge_pairs:
                    pair = pair.strip('()')
                    if pair:
                        u, v = map(int, pair.split(','))
                        edges.append((u, v))

        G = nx.Graph()
        G.add_edges_from(edges)

        networks.append({
            'id': row['id'],
            'class': row['class'],
            'adj_matrix': nx.to_numpy_array(G),
            'metrics': {
                'clustering': row['clustering'],
                'path_length': row['path_length'],
                'avg_degree': row['avg_degree']
            }
        })

    return networks

def save_results(results, filepath):
    """Save simulation results to JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Results saved to {filepath}")

def generate_checksum(filepath):
    """Generate SHA256 checksum for a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    """Main function to run the simulation pipeline."""
    parser = argparse.ArgumentParser(description='Simulate driven damped oscillators')
    parser.add_argument('--networks', type=str, default='data/raw/networks.csv',
                      help='Path to networks CSV file')
    parser.add_argument('--output', type=str, default='data/processed/simulation_results.json',
                      help='Path to output results JSON file')
    parser.add_argument('--damping', type=float, default=0.1, help='Damping coefficient')
    parser.add_argument('--driving_freq', type=float, default=1.0, help='Driving frequency')
    parser.add_argument('--driving_amp', type=float, default=1.0, help='Driving amplitude')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    args = parser.parse_args()

    logger.info(f"Loading networks from {args.networks}")
    try:
        networks = load_networks(args.networks)
        logger.info(f"Loaded {len(networks)} networks")
    except Exception as e:
        logger.error(f"Failed to load networks: {str(e)}")
        sys.exit(1)

    results = []
    failed_count = 0

    for graph_data in networks:
        logger.info(f"Simulating graph {graph_data['id']} ({graph_data['class']})")
        result = simulate_graph(
            graph_data,
            damping=args.damping,
            driving_freq=args.driving_freq,
            driving_amp=args.driving_amp,
            seed=args.seed
        )

        if result is None:
            failed_count += 1
            logger.error(f"Non-convergence or error for graph {graph_data['id']} - excluded from analysis")
            continue

        results.append(result)

    logger.info(f"Completed {len(results)} successful simulations, {failed_count} failed")

    if len(results) == 0:
        logger.error("No successful simulations. Exiting.")
        sys.exit(1)

    save_results(results, args.output)

    # Generate checksum
    checksum = generate_checksum(args.output)
    checksum_file = args.output + '.sha256'
    with open(checksum_file, 'w') as f:
        f.write(f"{checksum}  {os.path.basename(args.output)}\n")
    logger.info(f"Checksum saved to {checksum_file}")

    return results

if __name__ == '__main__':
    main()
