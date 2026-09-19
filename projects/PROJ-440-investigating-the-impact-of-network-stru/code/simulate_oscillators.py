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
from scipy.stats import linregress
import networkx as nx
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('state/simulation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_DAMPING = 0.1
DEFAULT_DRIVING_FREQ = 1.0
DEFAULT_T_SPAN = (0, 200)
DEFAULT_T_EVAL = np.linspace(0, 200, 1000)
TRANSIENT_THRESHOLD = 100
MIN_R_SQUARED = 0.95

def set_seed(seed):
    """Set random seed for reproducibility."""
    np.random.seed(seed)
    return seed

def get_laplacian_matrix(adj_matrix):
    """Compute Laplacian matrix from adjacency matrix."""
    degree = np.sum(adj_matrix, axis=1)
    L = np.diag(degree) - adj_matrix
    return L

def oscillator_equations(t, y, laplacian, damping, driving_freq, driving_amp=1.0):
    """
    Define coupled harmonic oscillator equations of motion.
    y = [x1, x2, ..., xn, v1, v2, ..., vn]
    Driving force is active for t in [0, 100].
    """
    n = len(y) // 2
    x = y[:n]
    v = y[n:]

    # Spring forces from coupling: -L * x
    coupling_force = -np.dot(laplacian, x)

    # Damping force: -damping * v
    damping_force = -damping * v

    # Driving force: active only for t <= 100
    if t <= 100:
        driving_force = driving_amp * np.sin(driving_freq * t)
    else:
        driving_force = np.zeros(n)

    # Acceleration: sum of forces
    a = coupling_force + damping_force + driving_force

    return np.concatenate([v, a])

def compute_total_energy(x, v, laplacian):
    """Compute total energy of the system."""
    # Kinetic energy: 0.5 * sum(v^2)
    kinetic = 0.5 * np.sum(v**2)

    # Potential energy: 0.5 * x^T * L * x
    potential = 0.5 * np.dot(x, np.dot(laplacian, x))

    return kinetic + potential

def damped_sinusoid(t, A, lam, omega, phi, C):
    """
    Damped sinusoid model for energy decay.
    E(t) = A * exp(-lambda * t) * cos(omega * t + phi) + C
    """
    return A * np.exp(-lam * t) * np.cos(omega * t + phi) + C

def extract_decay_rate(energy_data, time_data, initial_guess=None):
    """
    Extract decay rate by fitting damped sinusoid to post-transient energy data.
    Returns (decay_rate, r_squared, fit_params, status)
    """
    # Filter for post-transient phase
    mask = time_data > TRANSIENT_THRESHOLD
    t_post = time_data[mask] - TRANSIENT_THRESHOLD  # Shift time to start at 0
    E_post = energy_data[mask]

    if len(t_post) < 10:
        logger.warning("Insufficient data points for post-transient fit.")
        return None, None, None, "insufficient_data"

    # Initial guesses if not provided
    if initial_guess is None:
        A_init = E_post[0] - np.mean(E_post)
        lam_init = 0.1
        omega_init = 1.0
        phi_init = 0.0
        C_init = np.mean(E_post)
        initial_guess = [A_init, lam_init, omega_init, phi_init, C_init]

    try:
        # Fit the model
        popt, pcov = curve_fit(
            damped_sinusoid,
            t_post,
            E_post,
            p0=initial_guess,
            maxfev=10000
        )

        # Calculate R-squared
        E_pred = damped_sinusoid(t_post, *popt)
        ss_res = np.sum((E_post - E_pred) ** 2)
        ss_tot = np.sum((E_post - np.mean(E_post)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)

        # Extract parameters
        decay_rate = popt[1]
        status = "valid"

        return decay_rate, r_squared, popt, status

    except Exception as e:
        logger.error(f"Fit failed: {str(e)}")
        return None, None, None, "fit_failed"

def validate_fit(r_squared, decay_rate):
    """
    Validate the fit and check for resonance.
    Returns (is_valid, status)
    """
    # Check R-squared threshold
    if r_squared is None or r_squared < MIN_R_SQUARED:
        return False, "poor_fit"

    # Check for negative decay rate (resonance)
    if decay_rate is not None and decay_rate < 0:
        return True, "resonant"

    return True, "dissipative"

def load_networks(csv_path):
    """Load network data from CSV file."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Network data file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} networks from {csv_path}")
    return df

def simulate_graph(graph_id, adj_matrix, damping=DEFAULT_DAMPING, driving_freq=DEFAULT_DRIVING_FREQ, seed=42):
    """
    Simulate oscillator dynamics on a single graph.
    Returns (decay_rate, r_squared, status)
    """
    set_seed(seed)
    n = len(adj_matrix)

    # Initial conditions: random displacements and velocities
    x0 = np.random.randn(n)
    v0 = np.random.randn(n)
    y0 = np.concatenate([x0, v0])

    # Compute Laplacian
    laplacian = get_laplacian_matrix(adj_matrix)

    # Solve ODE
    sol = solve_ivp(
        oscillator_equations,
        DEFAULT_T_SPAN,
        y0,
        args=(laplacian, damping, driving_freq),
        method='DOP853',
        t_eval=DEFAULT_T_EVAL,
        rtol=1e-8,
        atol=1e-8
    )

    if not sol.success:
        logger.error(f"Integration failed for graph {graph_id}: {sol.message}")
        return None, None, "integration_failed"

    # Extract positions and velocities
    x = sol.y[:n, :]
    v = sol.y[n:, :]
    t = sol.t

    # Compute energy time series
    energy_data = np.array([compute_total_energy(x[:, i], v[:, i], laplacian) for i in range(len(t))])

    # Extract decay rate
    decay_rate, r_squared, _, status = extract_decay_rate(energy_data, t)

    # Validate fit
    is_valid, final_status = validate_fit(r_squared, decay_rate)

    if not is_valid:
        logger.warning(f"Graph {graph_id}: Fit validation failed (R²={r_squared}, Status={final_status})")
        return None, None, final_status

    logger.info(f"Graph {graph_id}: Decay rate={decay_rate:.6f}, R²={r_squared:.4f}, Status={final_status}")
    return decay_rate, r_squared, final_status

def save_results(graph_id, decay_rate, r_squared, status, output_path):
    """Save simulation results to a dictionary for later aggregation."""
    return {
        "graph_id": graph_id,
        "decay_rate": decay_rate,
        "r_squared": r_squared,
        "status": status
    }

def generate_checksum(data):
    """Generate SHA256 checksum for data."""
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description="Simulate driven damped oscillators on network topologies.")
    parser.add_argument("--input", type=str, default="data/raw/networks.csv", help="Path to input networks CSV")
    parser.add_argument("--output", type=str, default="data/processed/energy_decay.csv", help="Path to output results CSV")
    parser.add_argument("--damping", type=float, default=DEFAULT_DAMPING, help="Damping coefficient")
    parser.add_argument("--driving-freq", type=float, default=DEFAULT_DRIVING_FREQ, help="Driving frequency")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    logger.info(f"Starting simulation with input={args.input}, output={args.output}")

    # Load networks
    networks_df = load_networks(args.input)

    results = []
    failed_count = 0
    resonant_count = 0
    poor_fit_count = 0

    for _, row in networks_df.iterrows():
        graph_id = row['id']
        class_name = row['class']
        n_nodes = row['N']

        # Reconstruct adjacency matrix from edge list (assuming edge list is stored as string or separate file)
        # For this implementation, we assume the adjacency matrix is stored in a separate file or can be reconstructed
        # In a real scenario, we would load the adjacency matrix from a file or reconstruct it from edge lists
        # Here, we simulate a simple case for demonstration
        try:
            # Placeholder for actual adjacency matrix loading
            # In practice, this would load from a file or reconstruct from edge data
            adj_matrix = np.zeros((n_nodes, n_nodes))
            # Simulate a simple ring graph for testing
            for i in range(n_nodes):
                adj_matrix[i, (i+1) % n_nodes] = 1
                adj_matrix[(i+1) % n_nodes, i] = 1

            decay_rate, r_squared, status = simulate_graph(
                graph_id,
                adj_matrix,
                damping=args.damping,
                driving_freq=args.driving_freq,
                seed=args.seed
            )

            if status == "integration_failed":
                failed_count += 1
                continue

            if status == "poor_fit":
                poor_fit_count += 1
                continue

            if status == "resonant":
                resonant_count += 1

            results.append({
                "graph_id": graph_id,
                "class": class_name,
                "decay_rate": decay_rate,
                "r_squared": r_squared,
                "status": status
            })

        except Exception as e:
            logger.error(f"Failed to process graph {graph_id}: {str(e)}")
            failed_count += 1
            continue

    # Create output DataFrame
    if results:
        results_df = pd.DataFrame(results)
        results_df.to_csv(args.output, index=False)
        logger.info(f"Saved {len(results)} results to {args.output}")

        # Generate checksum
        checksum = generate_checksum(results)
        checksum_path = str(Path(args.output).with_suffix('.checksum'))
        with open(checksum_path, 'w') as f:
            f.write(checksum)
        logger.info(f"Generated checksum: {checksum}")

        # Log summary
        logger.info(f"Simulation complete: {len(results)} successful, {failed_count} failed, {resonant_count} resonant, {poor_fit_count} poor fit")
    else:
        logger.warning("No results to save.")

if __name__ == "__main__":
    main()