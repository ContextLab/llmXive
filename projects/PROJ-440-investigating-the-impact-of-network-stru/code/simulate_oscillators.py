import os
import sys
import json
import hashlib
import logging
import argparse
import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp
from scipy.optimize import curve_fit
from scipy.stats import pearsonr
import networkx as nx
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def set_seed(seed):
    """Set random seed for reproducibility."""
    np.random.seed(seed)
    return seed

def get_laplacian_matrix(graph):
    """Compute Laplacian matrix from NetworkX graph."""
    return nx.laplacian_matrix(graph).astype(float).toarray()

def oscillator_equations(t, y, adj_matrix, damping, driving_freq, natural_freq=1.0):
    """
    Compute derivatives for coupled harmonic oscillators.
    y = [x1, x2, ..., xn, v1, v2, ..., vn]
    """
    n = len(y) // 2
    x = y[:n]
    v = y[n:]

    # Coupling term: -L * x (Laplacian coupling)
    # Note: adj_matrix is the adjacency matrix, we need Laplacian
    # L = D - A
    degrees = np.sum(adj_matrix, axis=1)
    laplacian = np.diag(degrees) - adj_matrix

    # Coupling force: -k * L * x (assuming k=1)
    coupling_force = -np.dot(laplacian, x)

    # Damping: -damping * v
    damping_force = -damping * v

    # Driving force: F0 * sin(omega * t) applied to all nodes (or specific nodes)
    # For simplicity, apply to all nodes with same phase
    driving_force = np.sin(driving_freq * t)

    # Equations of motion
    dxdt = v
    dvdt = coupling_force + damping_force + driving_force

    return np.concatenate([dxdt, dvdt])

def compute_total_energy(y, adj_matrix, natural_freq=1.0):
    """
    Compute total energy of the system.
    E = 0.5 * sum(v^2) + 0.5 * sum(natural_freq^2 * x^2) + 0.5 * sum((x_i - x_j)^2)
    """
    n = len(y) // 2
    x = y[:n]
    v = y[n:]

    # Kinetic energy
    kinetic = 0.5 * np.sum(v**2)

    # Potential energy (spring)
    potential_spring = 0.5 * natural_freq**2 * np.sum(x**2)

    # Coupling potential energy (using adjacency matrix)
    # E_coupling = 0.5 * sum_{i,j} A_{ij} * (x_i - x_j)^2
    # = x^T * L * x (where L is Laplacian)
    degrees = np.sum(adj_matrix, axis=1)
    laplacian = np.diag(degrees) - adj_matrix
    coupling_potential = 0.5 * np.dot(x, np.dot(laplacian, x))

    return kinetic + potential_spring + coupling_potential

def damped_sinusoid(t, A, lambda_decay, omega, phi, C):
    """Damped sinusoid model for energy decay."""
    return A * np.exp(-lambda_decay * t) * np.cos(omega * t + phi) + C

def extract_decay_rate(energy_data, time_data):
    """
    Fit damped sinusoid to energy decay data and extract decay rate.
    Returns lambda_decay, r_squared, success status.
    """
    # Filter for post-transient phase (t > 100)
    mask = time_data > 100
    t_fit = time_data[mask]
    e_fit = energy_data[mask]

    if len(t_fit) < 10:
        logger.warning("Insufficient data points for fitting")
        return None, 0.0, False

    # Initial guess for parameters: A, lambda, omega, phi, C
    # Estimate from data
    A_guess = np.max(e_fit) - np.min(e_fit)
    lambda_guess = 0.01  # Small positive decay
    omega_guess = 1.0    # Natural frequency
    phi_guess = 0.0
    C_guess = np.min(e_fit)

    p0 = [A_guess, lambda_guess, omega_guess, phi_guess, C_guess]

    try:
        popt, pcov = curve_fit(
            damped_sinusoid, t_fit, e_fit, p0=p0,
            bounds=([0, -0.1, 0, -np.pi, 0], [np.inf, 0.1, 10, np.pi, np.inf]),
            maxfev=5000
        )

        # Calculate R-squared
        residuals = e_fit - damped_sinusoid(t_fit, *popt)
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((e_fit - np.mean(e_fit))**2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        lambda_decay = popt[1]

        return lambda_decay, r_squared, True

    except Exception as e:
        logger.warning(f"Fitting failed: {e}")
        return None, 0.0, False

def load_networks(csv_path):
    """Load network definitions from CSV."""
    df = pd.read_csv(csv_path)
    networks = []
    for _, row in df.iterrows():
        graph_id = row['id']
        graph_class = row['class']
        n_nodes = int(row['N'])
        # Reconstruct graph from edge list stored as JSON string
        edges = json.loads(row['edges'])
        G = nx.Graph()
        G.add_nodes_from(range(n_nodes))
        G.add_edges_from(edges)
        networks.append({
            'id': graph_id,
            'class': graph_class,
            'graph': G,
            'metrics': row.to_dict()
        })
    return networks

def simulate_graph(graph_data, damping=0.1, driving_freq=1.0, seed=42,
                   t_max=200, dt=0.1, transient_cutoff=100):
    """
    Simulate oscillator dynamics on a single graph.
    Returns time series of energy and fit results.
    """
    G = graph_data['graph']
    n = G.number_of_nodes()
    adj_matrix = nx.adjacency_matrix(G).astype(float).toarray()

    # Initial conditions: random positions and velocities
    x0 = np.random.randn(n) * 0.1
    v0 = np.random.randn(n) * 0.1
    y0 = np.concatenate([x0, v0])

    # Time points
    t_eval = np.arange(0, t_max, dt)

    # Solve ODE
    sol = solve_ivp(
        oscillator_equations,
        [0, t_max],
        y0,
        args=(adj_matrix, damping, driving_freq),
        t_eval=t_eval,
        method='RK45',
        rtol=1e-6,
        atol=1e-9
    )

    if not sol.success:
        raise RuntimeError(f"ODE solver failed: {sol.message}")

    # Compute energy at each time point
    energies = []
    for y in sol.y.T:
        e = compute_total_energy(y, adj_matrix)
        energies.append(e)
    energies = np.array(energies)

    # Extract decay rate
    lambda_decay, r_squared, fit_success = extract_decay_rate(energies, t_eval)

    # Determine status: resonant if decay rate is negative
    status = 'resonant' if (lambda_decay is not None and lambda_decay < 0) else 'dissipative'

    return {
        'graph_id': graph_data['id'],
        'class': graph_data['class'],
        'decay_rate': lambda_decay,
        'r_squared': r_squared,
        'fit_success': fit_success,
        'status': status,
        'energy_series': energies,
        'time_series': t_eval
    }

def validate_fit(result, min_r_squared=0.95):
    """Validate fit quality and flag issues."""
    if not result['fit_success']:
        return False, "Fit failed"
    if result['r_squared'] < min_r_squared:
        return False, f"R² ({result['r_squared']:.4f}) below threshold ({min_r_squared})"
    return True, "OK"

def save_results(results, output_path):
    """Save simulation results to CSV."""
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    logger.info(f"Results saved to {output_path}")

def generate_checksum(file_path):
    """Generate SHA256 checksum for a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    parser = argparse.ArgumentParser(description='Simulate driven damped oscillators on networks')
    parser.add_argument('--input', type=str, default='data/raw/networks.csv',
                        help='Input CSV with network definitions')
    parser.add_argument('--output', type=str, default='data/processed/energy_decay.csv',
                        help='Output CSV for simulation results')
    parser.add_argument('--damping', type=float, default=0.1,
                        help='Damping coefficient')
    parser.add_argument('--driving-freq', type=float, default=1.0,
                        help='Driving frequency')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed')
    parser.add_argument('--t-max', type=float, default=200.0,
                        help='Maximum simulation time')
    parser.add_argument('--dt', type=float, default=0.1,
                        help='Time step')
    args = parser.parse_args()

    # Load networks
    logger.info(f"Loading networks from {args.input}")
    networks = load_networks(args.input)
    logger.info(f"Loaded {len(networks)} networks")

    # Run simulations
    results = []
    for net in networks:
        try:
            logger.info(f"Simulating {net['id']} ({net['class']})")
            result = simulate_graph(
                net,
                damping=args.damping,
                driving_freq=args.driving_freq,
                seed=args.seed,
                t_max=args.t_max,
                dt=args.dt
            )
            results.append(result)
        except Exception as e:
            logger.error(f"Simulation failed for {net['id']}: {e}")
            # Log failure but continue with other graphs
            results.append({
                'graph_id': net['id'],
                'class': net['class'],
                'decay_rate': None,
                'r_squared': 0.0,
                'fit_success': False,
                'status': 'failed',
                'energy_series': None,
                'time_series': None
            })

    # Save results
    save_results(results, args.output)

    # Generate checksum
    checksum = generate_checksum(args.output)
    checksum_path = args.output + '.sha256'
    with open(checksum_path, 'w') as f:
        f.write(f"{checksum}  {args.output}\n")
    logger.info(f"Checksum saved to {checksum_path}")

    # Summary
    total = len(results)
    successful = sum(1 for r in results if r['fit_success'])
    resonant = sum(1 for r in results if r['status'] == 'resonant')
    dissipative = sum(1 for r in results if r['status'] == 'dissipative')
    failed = sum(1 for r in results if not r['fit_success'])

    logger.info(f"Simulation complete: {total} graphs, {successful} successful, "
                f"{resonant} resonant, {dissipative} dissipative, {failed} failed")

    return 0

if __name__ == '__main__':
    sys.exit(main())