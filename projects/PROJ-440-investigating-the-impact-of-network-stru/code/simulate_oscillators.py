import os
import sys
import json
import hashlib
import logging
import argparse
import numpy as np
from scipy.optimize import curve_fit
from scipy.integrate import solve_ivp
from scipy.stats import linregress
import networkx as nx
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('state/simulation.log')
    ]
)
logger = logging.getLogger(__name__)

def set_seed(seed: int) -> None:
    """Set random seed for reproducibility."""
    np.random.seed(seed)
    logger.info(f"Random seed set to {seed}")

def get_laplacian_matrix(adj_matrix: np.ndarray) -> np.ndarray:
    """Compute the Laplacian matrix from an adjacency matrix."""
    degree_matrix = np.diag(np.sum(adj_matrix, axis=1))
    return degree_matrix - adj_matrix

def oscillator_equations(t: float, y: np.ndarray, laplacian: np.ndarray, 
                         damping: float, driving_freq: float, 
                         driving_amplitude: float = 1.0) -> np.ndarray:
    """
    Define the equations of motion for driven damped oscillators.
    
    State vector y: [x1, x2, ..., xN, v1, v2, ..., vN]
    Equations:
      dx_i/dt = v_i
      dv_i/dt = -sum(L_ij * x_j) - damping * v_i + driving_amplitude * sin(driving_freq * t)
    """
    N = len(y) // 2
    positions = y[:N]
    velocities = y[N:]
    
    # Spring forces from Laplacian coupling
    spring_forces = -np.dot(laplacian, positions)
    
    # Damping forces
    damping_forces = -damping * velocities
    
    # External driving force (applied to all nodes for simplicity)
    driving_force = driving_amplitude * np.sin(driving_freq * t)
    
    accelerations = spring_forces + damping_forces + driving_force
    
    return np.concatenate([velocities, accelerations])

def compute_total_energy(t: float, y: np.ndarray, laplacian: np.ndarray, 
                         mass: float = 1.0, stiffness: float = 1.0) -> float:
    """
    Compute total energy (kinetic + potential) of the system.
    """
    N = len(y) // 2
    positions = y[:N]
    velocities = y[N:]
    
    # Kinetic energy: 0.5 * m * v^2
    kinetic = 0.5 * mass * np.sum(velocities**2)
    
    # Potential energy: 0.5 * x^T * L * x
    potential = 0.5 * np.dot(positions, np.dot(laplacian, positions))
    
    return kinetic + potential

def damped_sinusoid(t: np.ndarray, A: float, lambda_: float, omega: float, 
                    phi: float, C: float) -> np.ndarray:
    """
    Model function for damped sinusoid: E(t) = A * exp(-lambda * t) * cos(omega * t + phi) + C
    
    Parameters:
      A: Amplitude
      lambda_: Decay rate
      omega: Angular frequency
      phi: Phase shift
      C: Offset
    """
    return A * np.exp(-lambda_ * t) * np.cos(omega * t + phi) + C

def extract_decay_rate(t: np.ndarray, E: np.ndarray, transient_time: float = 100.0) -> Dict[str, Any]:
    """
    Extract energy decay rate by fitting a damped sinusoid to the post-transient phase.
    
    This function implements the core logic for T022a.
    
    Args:
        t: Time array
        E: Energy array
        transient_time: Time after which to start fitting (default 100)
        
    Returns:
        Dictionary with fitted parameters (A, lambda, omega, phi, C), R², and fit status.
    """
    # Filter for post-transient phase
    mask = t > transient_time
    t_post = t[mask]
    E_post = E[mask]
    
    if len(t_post) < 5:
        logger.warning("Insufficient data points after transient phase for fitting.")
        return {
            'status': 'insufficient_data',
            'r_squared': 0.0,
            'parameters': {}
        }
    
    # Initial guesses for curve_fit: [A, lambda, omega, phi, C]
    # A: estimated from max energy
    # lambda: estimated from decay over time
    # omega: estimated from frequency of oscillations
    # phi: 0
    # C: estimated from mean of last portion
    
    try:
        # Estimate initial parameters
        A_guess = np.max(E_post) - np.min(E_post)
        if A_guess == 0:
            A_guess = 1.0
            
        # Estimate decay rate from envelope
        # Use log of absolute deviation from mean to estimate decay
        E_mean = np.mean(E_post)
        E_dev = np.abs(E_post - E_mean)
        E_dev = np.maximum(E_dev, 1e-10)  # Avoid log(0)
        
        # Linear regression on log(E_dev) vs t to estimate decay
        log_E = np.log(E_dev)
        slope, _, _, _, _ = linregress(t_post, log_E)
        lambda_guess = -slope if slope < 0 else 0.1
        if lambda_guess <= 0:
            lambda_guess = 0.1
            
        # Estimate frequency from FFT
        if len(t_post) > 10:
            fft_vals = np.fft.fft(E_post - E_mean)
            freqs = np.fft.fftfreq(len(t_post), t_post[1] - t_post[0])
            positive_freqs = freqs[:len(freqs)//2]
            positive_magnitudes = np.abs(fft_vals[:len(fft_vals)//2])
            if np.max(positive_magnitudes) > 0:
                dominant_freq_idx = np.argmax(positive_magnitudes)
                omega_guess = 2 * np.pi * positive_freqs[dominant_freq_idx]
                if omega_guess <= 0:
                    omega_guess = 1.0
            else:
                omega_guess = 1.0
        else:
            omega_guess = 1.0
            
        phi_guess = 0.0
        C_guess = E_mean
        
        initial_guess = [A_guess, lambda_guess, omega_guess, phi_guess, C_guess]
        
        # Bounds to keep parameters physical
        # A > 0, lambda >= 0, omega > 0, phi in [-pi, pi], C in reasonable range
        lower_bounds = [0.0, 0.0, 0.0, -np.pi, -np.inf]
        upper_bounds = [np.inf, 10.0, 100.0, np.pi, np.inf]
        
        popt, pcov = curve_fit(
            damped_sinusoid, 
            t_post, 
            E_post, 
            p0=initial_guess, 
            bounds=(lower_bounds, upper_bounds),
            maxfev=10000
        )
        
        A, lambda_, omega, phi, C = popt
        
        # Calculate R²
        E_pred = damped_sinusoid(t_post, *popt)
        ss_res = np.sum((E_post - E_pred) ** 2)
        ss_tot = np.sum((E_post - np.mean(E_post)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
        
        return {
            'status': 'success',
            'r_squared': float(r_squared),
            'parameters': {
                'A': float(A),
                'lambda': float(lambda_),
                'omega': float(omega),
                'phi': float(phi),
                'C': float(C)
            },
            'covariance': pcov.tolist() if pcov is not None else None
        }
        
    except Exception as e:
        logger.error(f"Curve fitting failed: {str(e)}")
        return {
            'status': 'fit_failed',
            'error': str(e),
            'r_squared': 0.0,
            'parameters': {}
        }

def validate_fit(result: Dict[str, Any], r_squared_threshold: float = 0.95) -> bool:
    """
    Validate the quality of the fit based on R².
    
    Args:
        result: Output from extract_decay_rate
        r_squared_threshold: Minimum acceptable R² value
        
    Returns:
        True if fit is valid, False otherwise
    """
    if result['status'] != 'success':
        return False
    return result['r_squared'] >= r_squared_threshold

def load_networks(csv_path: str) -> List[Dict[str, Any]]:
    """
    Load network data from CSV file.
    
    Args:
        csv_path: Path to the CSV file containing network data
        
    Returns:
        List of dictionaries, each representing a network
    """
    import pandas as pd
    df = pd.read_csv(csv_path)
    networks = []
    for _, row in df.iterrows():
        networks.append(row.to_dict())
    return networks

def simulate_graph(graph_id: str, adj_matrix: np.ndarray, damping: float = 0.1, 
                   driving_freq: float = 1.0, driving_amplitude: float = 1.0,
                   simulation_time: float = 200.0, transient_time: float = 100.0,
                   seed: int = 42) -> Dict[str, Any]:
    """
    Simulate driven damped oscillator dynamics on a given graph.
    
    Args:
        graph_id: Unique identifier for the graph
        adj_matrix: Adjacency matrix of the graph
        damping: Damping coefficient
        driving_freq: Frequency of external driving force
        driving_amplitude: Amplitude of external driving force
        simulation_time: Total simulation time
        transient_time: Time after which to start analyzing decay
        seed: Random seed for initial conditions
        
    Returns:
        Dictionary containing simulation results
    """
    set_seed(seed)
    
    N = adj_matrix.shape[0]
    laplacian = get_laplacian_matrix(adj_matrix)
    
    # Initial conditions: random positions and velocities
    y0 = np.random.randn(2 * N)
    
    # Time points for integration
    t_eval = np.linspace(0, simulation_time, 2000)
    
    # Solve ODE
    try:
        sol = solve_ivp(
            lambda t, y: oscillator_equations(t, y, laplacian, damping, driving_freq, driving_amplitude),
            [0, simulation_time],
            y0,
            method='DOP853',
            t_eval=t_eval,
            rtol=1e-6,
            atol=1e-9
        )
        
        if not sol.success:
            raise RuntimeError(f"Integration failed: {sol.message}")
        
        # Compute energy at each time point
        energies = np.array([compute_total_energy(t, sol.y[:, i], laplacian) 
                             for i, t in enumerate(sol.t)])
        
        # Extract decay rate
        decay_result = extract_decay_rate(sol.t, energies, transient_time)
        
        return {
            'graph_id': graph_id,
            'decay_rate': decay_result['parameters'].get('lambda', None),
            'r_squared': decay_result['r_squared'],
            'status': 'dissipative' if decay_result['status'] == 'success' and decay_result['r_squared'] >= 0.95 else 'fit_failed',
            'fit_parameters': decay_result['parameters'],
            'convergence_std': None  # Will be computed in convergence tests
        }
        
    except Exception as e:
        logger.error(f"Simulation failed for graph {graph_id}: {str(e)}")
        return {
            'graph_id': graph_id,
            'decay_rate': None,
            'r_squared': 0.0,
            'status': 'simulation_failed',
            'error': str(e),
            'fit_parameters': {}
        }

def save_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save simulation results to a JSON file.
    
    Args:
        results: List of result dictionaries
        output_path: Path to the output JSON file
    """
    import json
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")

def generate_checksum(file_path: str) -> str:
    """
    Generate SHA256 checksum for a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hexadecimal checksum string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    """
    Main entry point for the simulation script.
    """
    parser = argparse.ArgumentParser(description='Simulate driven damped oscillators on networks')
    parser.add_argument('--input-csv', type=str, required=True, 
                        help='Path to input networks CSV file')
    parser.add_argument('--output-json', type=str, required=True,
                        help='Path to output results JSON file')
    parser.add_argument('--damping', type=float, default=0.1,
                        help='Damping coefficient')
    parser.add_argument('--driving-freq', type=float, default=1.0,
                        help='Driving frequency')
    parser.add_argument('--driving-amplitude', type=float, default=1.0,
                        help='Driving amplitude')
    parser.add_argument('--simulation-time', type=float, default=200.0,
                        help='Total simulation time')
    parser.add_argument('--transient-time', type=float, default=100.0,
                        help='Time after which to start analyzing decay')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed')
    
    args = parser.parse_args()
    
    logger.info(f"Starting simulation with input: {args.input_csv}")
    
    # Load networks
    networks = load_networks(args.input_csv)
    logger.info(f"Loaded {len(networks)} networks")
    
    results = []
    for network in networks:
        graph_id = str(network.get('id', 'unknown'))
        
        # Reconstruct adjacency matrix from edge list or other representation
        # Assuming network data contains edge list or adjacency information
        # For now, we'll create a simple example
        N = int(network.get('N', 10))
        
        # This is a placeholder - in reality, you'd reconstruct the graph
        # from the network data (e.g., edge list, adjacency matrix, etc.)
        # For demonstration, we'll create a random graph
        try:
            # Attempt to reconstruct graph from stored data
            # This would depend on how networks were saved in T015
            adj_matrix = np.zeros((N, N))
            
            # If edge list is available in network data
            if 'edges' in network:
                edges = network['edges']
                for u, v in edges:
                    adj_matrix[u, v] = 1
                    adj_matrix[v, u] = 1
            else:
                # Fallback: create a simple ring graph for testing
                for i in range(N):
                    adj_matrix[i, (i+1) % N] = 1
                    adj_matrix[(i+1) % N, i] = 1
            
            # Run simulation
            result = simulate_graph(
                graph_id=graph_id,
                adj_matrix=adj_matrix,
                damping=args.damping,
                driving_freq=args.driving_freq,
                driving_amplitude=args.driving_amplitude,
                simulation_time=args.simulation_time,
                transient_time=args.transient_time,
                seed=args.seed
            )
            results.append(result)
            
        except Exception as e:
            logger.error(f"Failed to process network {graph_id}: {str(e)}")
            results.append({
                'graph_id': graph_id,
                'status': 'processing_failed',
                'error': str(e)
            })
    
    # Save results
    save_results(results, args.output_json)
    
    # Generate checksum
    checksum = generate_checksum(args.output_json)
    logger.info(f"Output checksum: {checksum}")

if __name__ == "__main__":
    main()