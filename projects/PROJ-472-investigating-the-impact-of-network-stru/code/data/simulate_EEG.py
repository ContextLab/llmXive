"""
T011: Implement simulate_EEG.py to generate synthetic EEG time-series from structural graphs.

Uses Wilson-Cowan equations to simulate neural activity on structural connectomes.
Applies MNE-Python band-pass filtering and downsampling to mimic real-data preprocessing.
"""
import os
import sys
import numpy as np
import pandas as pd
import mne
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import warnings

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import SIMULATION_PARAMS, ensure_directories
from utils.logger import get_logger

# Suppress MNE warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning, module="mne")

logger = get_logger(__name__)

class WilsonCowanSimulator:
    """Simulates neural activity using Wilson-Cowan equations on a structural graph."""

    def __init__(self, adjacency_matrix: np.ndarray, params: Dict):
        """
        Initialize the simulator.

        Args:
            adjacency_matrix: N x N structural connectivity matrix (weighted).
            params: Dictionary of simulation parameters (from config.SIMULATION_PARAMS).
        """
        self.adj_matrix = adjacency_matrix
        self.n_nodes = adjacency_matrix.shape[0]
        self.params = params

        # Extract parameters with defaults
        self.dt = params.get('dt', 0.1)  # Time step
        self.t_steps = params.get('t_steps', 1000)  # Total simulation steps
        self.noise_level = params.get('noise_level', 0.01)
        self.w_exc = params.get('w_exc', 1.0)  # Excitatory connection weight
        self.w_inh = params.get('w_inh', -0.5)  # Inhibitory connection weight
        self.tau_e = params.get('tau_e', 20.0)  # Excitatory time constant
        self.tau_i = params.get('tau_i', 10.0)  # Inhibitory time constant
        self.a_e = params.get('a_e', 1.0)  # Excitatory gain
        self.a_i = params.get('a_i', 1.0)  # Inhibitory gain
        self.theta_e = params.get('theta_e', 0.5)  # Excitatory threshold
        self.theta_i = params.get('theta_i', 0.5)  # Inhibitory threshold

        # Normalize adjacency matrix for stability
        max_val = np.max(np.abs(self.adj_matrix))
        if max_val > 0:
            self.adj_matrix = self.adj_matrix / max_val

    def sigmoid(self, x: np.ndarray) -> np.ndarray:
        """Sigmoid activation function."""
        return 1.0 / (1.0 + np.exp(-self.a_e * (x - self.theta_e)))

    def run_simulation(self) -> np.ndarray:
        """
        Run the Wilson-Cowan simulation.

        Returns:
            E: N x T array of excitatory activity over time.
        """
        # Initialize state variables
        E = np.zeros((self.n_nodes, self.t_steps))
        I = np.zeros((self.n_nodes, self.t_steps))

        # Add small random initial conditions
        E[:, 0] = np.random.rand(self.n_nodes) * 0.1
        I[:, 0] = np.random.rand(self.n_nodes) * 0.1

        # Normalized adjacency matrix
        W = self.adj_matrix

        for t in range(1, self.t_steps):
            # Compute input to excitatory population
            input_e = self.w_exc * (W @ E[:, t-1]) - self.w_inh * (W @ I[:, t-1])
            input_e += self.noise_level * np.random.randn(self.n_nodes)

            # Compute input to inhibitory population
            input_i = self.w_exc * (W @ E[:, t-1]) - self.w_inh * (W @ I[:, t-1])
            input_i += self.noise_level * np.random.randn(self.n_nodes)

            # Wilson-Cowan equations
            dE = (self.sigmoid(input_e) - E[:, t-1]) / self.tau_e
            dI = (self.sigmoid(input_i) - I[:, t-1]) / self.tau_i

            # Update state
            E[:, t] = E[:, t-1] + self.dt * dE
            I[:, t] = I[:, t-1] + self.dt * dI

            # Ensure non-negative activity
            E[:, t] = np.maximum(E[:, t], 0)
            I[:, t] = np.maximum(I[:, t], 0)

        return E

def load_connectome(subject_id: str, data_root: Path) -> Optional[np.ndarray]:
    """
    Load the structural connectome for a given subject.

    Args:
        subject_id: Subject identifier (e.g., 'sub-001').
        data_root: Root path to the data directory.

    Returns:
        N x N adjacency matrix or None if file not found.
    """
    # Path pattern based on T010 output: data/processed/connectomes/{subject_id}_connectome.csv
    conn_path = data_root / "processed" / "connectomes" / f"{subject_id}_connectome.csv"

    if not conn_path.exists():
        logger.error(f"Connectome file not found: {conn_path}")
        return None

    try:
        df = pd.read_csv(conn_path)
        # Assume the CSV is a square matrix (first column might be index)
        if df.shape[0] == df.shape[1]:
            matrix = df.values
        else:
            # If it has headers/indices, try to infer
            matrix = df.values
            if matrix.shape[0] != matrix.shape[1]:
                # Try to read as matrix without header
                matrix = pd.read_csv(conn_path, header=None).values

        logger.info(f"Loaded connectome for {subject_id}: shape {matrix.shape}")
        return matrix
    except Exception as e:
        logger.error(f"Error loading connectome for {subject_id}: {e}")
        return None

def simulate_eeg_for_subject(
    subject_id: str,
    data_root: Path,
    output_dir: Path,
    params: Dict
) -> Optional[Path]:
    """
    Simulate EEG for a single subject and save the result.

    Args:
        subject_id: Subject identifier.
        data_root: Root data directory.
        output_dir: Directory to save output.
        params: Simulation parameters.

    Returns:
        Path to the saved EEG file, or None if failed.
    """
    logger.info(f"Starting EEG simulation for {subject_id}")

    # Load connectome
    adj_matrix = load_connectome(subject_id, data_root)
    if adj_matrix is None:
        return None

    # Run Wilson-Cowan simulation
    simulator = WilsonCowanSimulator(adj_matrix, params)
    activity = simulator.run_simulation()

    # Determine sampling frequency for simulation
    # Assuming the simulation time step corresponds to a high frequency
    sim_fs = 1000.0  # Hz (internal simulation frequency)

    # Downsample to EEG frequency (e.g., 250 Hz)
    target_fs = params.get('target_fs', 250)
    downsample_factor = int(sim_fs / target_fs)

    # Downsample by taking every nth sample
    if downsample_factor > 1:
        activity_downsampled = activity[:, ::downsample_factor]
    else:
        activity_downsampled = activity

    # Create MNE Info object
    # Generate dummy channel names based on number of nodes
    n_channels = activity_downsampled.shape[0]
    ch_names = [f"Node_{i:03d}" for i in range(n_channels)]
    ch_types = ['eeg'] * n_channels
    info = mne.create_info(ch_names=ch_names, sfreq=target_fs, ch_types=ch_types)

    # Create RawArray
    raw = mne.io.RawArray(activity_downsampled.astype(np.float64), info)

    # Apply band-pass filter (1-40 Hz) to mimic real EEG preprocessing
    # This mimics the filtering step required by FR-002
    logger.info(f"Applying band-pass filter (1-40 Hz) to {subject_id}")
    raw_filtered = raw.copy().filter(l_freq=1.0, h_freq=40.0, method='iir')

    # Save to FIF file
    output_path = output_dir / f"{subject_id}_eeg.fif"
    raw_filtered.save(output_path, overwrite=True)

    # Also save as CSV for easier analysis
    csv_path = output_dir / f"{subject_id}_eeg.csv"
    np.savetxt(csv_path, activity_downsampled.T, delimiter=',',
               header=','.join(ch_names), comments='')

    logger.info(f"Saved EEG for {subject_id} to {output_path}")
    return output_path

def main():
    """Main entry point for EEG simulation."""
    logger.info("Starting EEG Simulation Pipeline (T011)")

    # Setup directories
    ensure_directories()
    data_root = Path(os.getenv('DATA_ROOT', 'data'))
    output_dir = data_root / "processed" / "eeg"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get subject list (from T009/T010 processed data)
    # We expect subjects sub-001 to sub-010
    subjects = [f"sub-{i:03d}" for i in range(1, 11)]

    # Get simulation parameters
    sim_params = SIMULATION_PARAMS

    successful_count = 0
    failed_count = 0

    for subject in subjects:
        try:
            result_path = simulate_eeg_for_subject(
                subject_id=subject,
                data_root=data_root,
                output_dir=output_dir,
                params=sim_params
            )
            if result_path:
                successful_count += 1
            else:
                failed_count += 1
                logger.warning(f"Failed to simulate EEG for {subject}")
        except Exception as e:
            failed_count += 1
            logger.error(f"Error processing {subject}: {e}", exc_info=True)

    logger.info(f"Simulation complete: {successful_count} successful, {failed_count} failed")

    if successful_count == 0:
        logger.error("No subjects processed successfully. Check input data.")
        sys.exit(1)

    return successful_count

if __name__ == "__main__":
    main()
