"""
simulate_oscillators.py

Implements the numerical simulation of driven, damped coupled harmonic oscillators
on network topologies to extract energy dissipation rates.

Defines the equations of motion using the graph Laplacian, integrates the system
using scipy.integrate.solve_ivp, and extracts decay rates from the energy envelope.
"""

import os
import sys
import json
import hashlib
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Callable

import numpy as np
import pandas as pd
from scipy import integrate, stats
from scipy.optimize import curve_fit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/simulation.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Ensure logs directory exists
Path('logs').mkdir(exist_ok=True)


def set_seed(seed: int) -> None:
    """Set random seed for reproducibility."""
    np.random.seed(seed)


def get_laplacian_matrix(graph: Any) -> np.ndarray:
    """
    Compute the Laplacian matrix of a graph.

    Args:
        graph: A NetworkX graph object.

    Returns:
        np.ndarray: The Laplacian matrix L = D - A.
    """
    import networkx as nx
    L = nx.laplacian_matrix(graph).toarray()
    return L


def oscillator_equations(t: float, y: np.ndarray, L: np.ndarray,
                         damping: float, driving_amplitude: float,
                         driving_freq: float, natural_freq: float) -> np.ndarray:
    """
    Define the equations of motion for the driven, damped coupled oscillator system.

    The system is defined by:
    x''_i = -damping * x'_i - natural_freq^2 * x_i - sum_j(L_ij * x_j) + F_drive(t)

    State vector y = [x_1, ..., x_N, v_1, ..., v_N]
    where x are positions and v are velocities.

    Args:
        t: Current time.
        y: State vector [x_1...x_N, v_1...v_N].
        L: Laplacian matrix (N x N).
        damping: Damping coefficient (gamma).
        driving_amplitude: Amplitude of external driving force (F0).
        driving_freq: Frequency of external driving force (omega_d).
        natural_freq: Natural frequency of individual oscillators (omega_0).

    Returns:
        np.ndarray: Derivatives [v_1...v_N, a_1...a_N].
    """
    N = len(y) // 2
    x = y[:N]
    v = y[N:]

    # Coupling term: -L @ x
    coupling_force = -L @ x

    # Damping term: -damping * v
    damping_force = -damping * v

    # Restoring force: -natural_freq^2 * x
    restoring_force = -(natural_freq ** 2) * x

    # Driving force: F0 * cos(omega_d * t)
    # Apply driving force to all nodes (or could be selective)
    drive_force = driving_amplitude * np.cos(driving_freq * t)

    # Acceleration
    a = restoring_force + coupling_force + damping_force + drive_force

    dydt = np.concatenate([v, a])
    return dydt


def compute_total_energy(y: np.ndarray, L: np.ndarray, natural_freq: float) -> float:
    """
    Compute the total energy of the system at a given state.

    E = 0.5 * sum(v_i^2) + 0.5 * natural_freq^2 * sum(x_i^2) + 0.5 * x^T L x

    Args:
        y: State vector [x, v].
        L: Laplacian matrix.
        natural_freq: Natural frequency.

    Returns:
        float: Total energy.
    """
    N = len(y) // 2
    x = y[:N]
    v = y[N:]

    kinetic = 0.5 * np.sum(v ** 2)
    potential_onsite = 0.5 * (natural_freq ** 2) * np.sum(x ** 2)
    potential_coupling = 0.5 * np.dot(x, L @ x)

    return kinetic + potential_onsite + potential_coupling


def damped_sinusoid(t: np.ndarray, A: float, lambda_decay: float,
                    omega: float, phi: float, C: float) -> np.ndarray:
    """
    Model function for damped sinusoidal decay: E(t) = A * exp(-lambda*t) * cos(omega*t + phi) + C

    Note: In many physical contexts, the energy envelope decays as exp(-2*gamma*t).
    Here we fit the envelope directly or the oscillating energy if appropriate.
    For this task, we fit the total energy which oscillates around a decaying trend.
    """
    return A * np.exp(-lambda_decay * t) * np.cos(omega * t + phi) + C


def extract_decay_rate(t: np.ndarray, energy: np.ndarray,
                       min_t: float = 100.0) -> Tuple[Optional[float], float, str]:
    """
    Extract the decay rate (lambda) from the energy time series by fitting a damped sinusoid
    to the post-transient phase (t > min_t).

    Args:
        t: Time array.
        energy: Total energy array.
        min_t: Time after which to start fitting (transient cutoff).

    Returns:
        Tuple[lambda, r_squared, status]:
            - lambda: Estimated decay rate (None if fit failed).
            - r_squared: R-squared value of the fit.
            - status: "success", "resonant" (if lambda < 0), or "failed".
    """
    mask = t >= min_t
    t_fit = t[mask]
    e_fit = energy[mask]

    if len(t_fit) < 10:
        return None, 0.0, "failed_insufficient_data"

    # Initial guesses for [A, lambda, omega, phi, C]
    # A: amplitude of oscillation
    # lambda: decay rate (expected positive)
    # omega: frequency (approx natural freq)
    # phi: phase
    # C: offset

    # Estimate initial parameters
    e_mean = np.mean(e_fit)
    e_std = np.std(e_fit)
    A_guess = e_std
    lambda_guess = 0.01  # Small positive decay
    omega_guess = 1.0    # Approx natural freq
    phi_guess = 0.0
    C_guess = e_mean

    p0 = [A_guess, lambda_guess, omega_guess, phi_guess, C_guess]

    try:
        # Bounds: A > 0, lambda > -1 (allow negative for resonance detection), omega > 0
        # We allow lambda to go negative to detect resonance
        p_bounds = (
            [0, -1.0, 0.1, -np.pi, -np.inf],  # Lower bounds
            [np.inf, 10.0, 10.0, np.pi, np.inf] # Upper bounds
        )

        popt, pcov = curve_fit(
            damped_sinusoid, t_fit, e_fit, p0=p0, bounds=p_bounds,
            maxfev=10000
        )

        A_fit, lambda_fit, omega_fit, phi_fit, C_fit = popt

        # Calculate R-squared
        e_pred = damped_sinusoid(t_fit, *popt)
        ss_res = np.sum((e_fit - e_pred) ** 2)
        ss_tot = np.sum((e_fit - np.mean(e_fit)) ** 2)

        if ss_tot == 0:
            r_squared = 1.0
        else:
            r_squared = 1 - (ss_res / ss_tot)

        status = "success"
        if lambda_fit < 0:
            status = "resonant"

        return lambda_fit, r_squared, status

    except Exception as e:
        logger.warning(f"Curve fit failed: {e}")
        return None, 0.0, "fit_failed"


def simulate_graph(graph_data: Dict[str, Any],
                   damping: float = 0.1,
                   driving_amplitude: float = 0.5,
                   driving_freq: float = 1.0,
                   natural_freq: float = 1.0,
                   total_time: float = 200.0,
                   transient_time: float = 100.0,
                   num_points: int = 2000,
                   seed: int = 42) -> Dict[str, Any]:
    """
    Simulate the oscillator dynamics on a single graph.

    Args:
        graph_data: Dictionary containing 'id', 'class', 'adjacency' (or similar).
        damping: Damping coefficient.
        driving_amplitude: Driving force amplitude.
        driving_freq: Driving frequency.
        natural_freq: Natural frequency of oscillators.
        total_time: Total simulation time.
        transient_time: Time to exclude from decay analysis.
        num_points: Number of time points for output.
        seed: Random seed for initial conditions.

    Returns:
        Dictionary with decay rate, R-squared, status, and simulation metadata.
    """
    set_seed(seed)

    # Reconstruct graph from adjacency matrix or edge list if needed
    # Assuming graph_data contains an adjacency matrix 'adj' or similar
    import networkx as nx
    adj = graph_data.get('adjacency')
    if adj is None:
        raise ValueError("Graph data must contain 'adjacency' matrix.")

    adj = np.array(adj)
    N = adj.shape[0]
    L = get_laplacian_matrix(nx.from_numpy_array(adj))

    # Initial conditions: random small displacements and velocities
    x0 = np.random.normal(0, 0.1, N)
    v0 = np.random.normal(0, 0.1, N)
    y0 = np.concatenate([x0, v0])

    t_eval = np.linspace(0, total_time, num_points)

    # Integrate
    sol = integrate.solve_ivp(
        fun=lambda t, y: oscillator_equations(
            t, y, L, damping, driving_amplitude, driving_freq, natural_freq
        ),
        t_span=(0, total_time),
        y0=y0,
        method='RK45',
        t_eval=t_eval,
        rtol=1e-6,
        atol=1e-9
    )

    if not sol.success:
        raise RuntimeError(f"Integration failed: {sol.message}")

    # Compute energy time series
    energies = np.array([compute_total_energy(sol.y[:, i], L, natural_freq) for i in range(len(t_eval))])

    # Extract decay rate
    lambda_decay, r_squared, status = extract_decay_rate(
        t_eval, energies, min_t=transient_time
    )

    return {
        'graph_id': graph_data.get('id', 'unknown'),
        'graph_class': graph_data.get('class', 'unknown'),
        'damping': damping,
        'driving_freq': driving_freq,
        'decay_rate': lambda_decay,
        'r_squared': r_squared,
        'status': status,
        'num_nodes': N,
        'simulation_time': total_time
    }


def load_networks(filepath: str) -> List[Dict[str, Any]]:
    """
    Load network data from a CSV file generated by generate_networks.py.

    Args:
        filepath: Path to data/raw/networks.csv.

    Returns:
        List of dictionaries, each representing a network instance.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Network file not found: {filepath}")

    df = pd.read_csv(filepath)
    networks = []

    for _, row in df.iterrows():
        # Reconstruct adjacency matrix from edge list or similar if stored that way
        # For now, assume the CSV has a serialized adjacency matrix or we need to regenerate
        # Since generate_networks.py likely stores metrics, we need the graph structure.
        # We will assume the CSV has an 'adjacency' column (serialized list of lists)
        # OR we need to regenerate the graph based on parameters if stored.
        # Looking at T015, it exports to CSV. We assume the CSV has the necessary structure.
        # If 'adjacency' is not in CSV, we might need to store it differently or regenerate.
        # For robustness, we assume the CSV contains the adjacency matrix as a string or list.
        
        adj_str = row.get('adjacency')
        if adj_str is None:
            # Fallback: if adjacency is not stored, we cannot simulate directly from this CSV
            # unless we have a way to regenerate the graph.
            # Assuming for this task that the CSV contains the adjacency matrix.
            raise ValueError(f"Missing 'adjacency' column in {filepath} for graph {row.get('id')}")

        try:
            adj = np.array(json.loads(adj_str))
        except json.JSONDecodeError:
            raise ValueError(f"Invalid adjacency format for graph {row.get('id')}")

        networks.append({
            'id': row['id'],
            'class': row['class'],
            'adjacency': adj
        })

    return networks


def save_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save simulation results to a CSV file.

    Args:
        results: List of result dictionaries.
        output_path: Path to output CSV.
    """
    df = pd.DataFrame(results)
    # Ensure columns match schema
    expected_cols = ['graph_id', 'graph_class', 'damping', 'driving_freq', 
                     'decay_rate', 'r_squared', 'status', 'num_nodes', 'simulation_time']
    # Reorder if necessary
    if all(col in df.columns for col in expected_cols):
        df = df[expected_cols]
    
    df.to_csv(output_path, index=False)
    
    # Generate checksum
    from code.utils.checksums import generate_checksum_file
    generate_checksum_file(output_path)
    logger.info(f"Results saved to {output_path} with checksum.")


def main():
    """Main entry point for the simulation pipeline."""
    parser = argparse.ArgumentParser(description="Simulate driven oscillators on networks.")
    parser.add_argument('--input', type=str, default='data/raw/networks.csv',
                        help='Path to input networks CSV')
    parser.add_argument('--output', type=str, default='data/processed/energy_decay.csv',
                        help='Path to output results CSV')
    parser.add_argument('--damping', type=float, default=0.1,
                        help='Damping coefficient')
    parser.add_argument('--driving-freq', type=float, default=1.0,
                        help='Driving frequency')
    parser.add_argument('--total-time', type=float, default=200.0,
                        help='Total simulation time')
    parser.add_argument('--transient-time', type=float, default=100.0,
                        help='Transient time to exclude from fit')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for initial conditions')

    args = parser.parse_args()

    logger.info(f"Loading networks from {args.input}")
    try:
        networks = load_networks(args.input)
    except Exception as e:
        logger.error(f"Failed to load networks: {e}")
        sys.exit(1)

    logger.info(f"Loaded {len(networks)} networks. Starting simulation...")

    results = []
    for i, net in enumerate(networks):
        logger.info(f"Simulating graph {i+1}/{len(networks)}: {net['id']} ({net['class']})")
        try:
            res = simulate_graph(
                net,
                damping=args.damping,
                driving_amplitude=0.5,
                driving_freq=args.driving_freq,
                natural_freq=1.0,
                total_time=args.total_time,
                transient_time=args.transient_time,
                seed=args.seed + i
            )
            results.append(res)
        except Exception as e:
            logger.error(f"Simulation failed for {net['id']}: {e}")
            # Log failure but continue
            results.append({
                'graph_id': net['id'],
                'graph_class': net['class'],
                'damping': args.damping,
                'driving_freq': args.driving_freq,
                'decay_rate': None,
                'r_squared': 0.0,
                'status': 'failed',
                'num_nodes': net['adjacency'].shape[0],
                'simulation_time': args.total_time
            })

    logger.info(f"Simulation complete. Saving {len(results)} results to {args.output}")
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    save_results(results, args.output)

    logger.info("Done.")


if __name__ == '__main__':
    main()