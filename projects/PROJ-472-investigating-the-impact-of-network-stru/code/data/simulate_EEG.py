import os
import sys
import numpy as np
import pandas as pd
import mne
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import hashlib
from datetime import datetime

# Import from project API surface
from config import get_data_root, ensure_directories
from data.models import Participant, StructuralConnectome, AvalancheRecord
from utils.logger import get_logger, log_pipeline_start, log_pipeline_end, handle_exceptions, SimulationError
from utils.env_config import get_simulation_seed
from data.store import load_connectome_matrix

# Configure logging
logger = get_logger(__name__)

# Wilson-Cowan Parameters (Default, can be overridden by config)
DEFAULT_WC_PARAMS = {
    "excitatory_gain": 1.0,
    "inhibitory_gain": 1.0,
    "time_constant_exc": 10.0,
    "time_constant_inh": 20.0,
    "external_input_exc": 0.5,
    "external_input_inh": 0.5,
    "noise_std": 0.01,
    "dt": 0.001,
    "duration": 10.0,  # seconds
    "sampling_rate": 250  # Hz (downsampled to this later)
}

class WilsonCowanSimulator:
    """
    Simulates neural activity using Wilson-Cowan equations on a structural connectome.
    """
    def __init__(self, params: Optional[Dict[str, float]] = None, seed: Optional[int] = None):
        self.params = {**DEFAULT_WC_PARAMS, **(params or {})}
        self.seed = seed
        self.rng = np.random.default_rng(self.seed)
        
        # Validate parameters
        if self.params["dt"] <= 0:
            raise SimulationError("Time step (dt) must be positive.")
        if self.params["duration"] <= 0:
            raise SimulationError("Duration must be positive.")

    def _sigmoid(self, x: np.ndarray, gain: float) -> np.ndarray:
        """Sigmoid activation function."""
        return 1.0 / (1.0 + np.exp(-gain * x))

    def simulate(self, connectivity_matrix: np.ndarray, num_nodes: int) -> np.ndarray:
        """
        Run Wilson-Cowan simulation for a given connectivity matrix.
        
        Args:
            connectivity_matrix: Adjacency matrix of structural connectome (N x N).
            num_nodes: Number of nodes in the network.
        
        Returns:
            np.ndarray: Time series of neural activity (num_nodes x num_timepoints).
        """
        dt = self.params["dt"]
        T = self.params["duration"]
        num_steps = int(T / dt)
        
        # Initialize state variables (E: Excitatory, I: Inhibitory)
        E = np.zeros((num_nodes, num_steps))
        I = np.zeros((num_nodes, num_steps))
        
        # Initial conditions (small random perturbation)
        E[:, 0] = self.rng.uniform(0.01, 0.02, num_nodes)
        I[:, 0] = self.rng.uniform(0.01, 0.02, num_nodes)
        
        # Parameters
        J = self.params["excitatory_gain"] * connectivity_matrix
        W = self.params["inhibitory_gain"] * connectivity_matrix
        tau_E = self.params["time_constant_exc"]
        tau_I = self.params["time_constant_inh"]
        I_ext_E = self.params["external_input_exc"]
        I_ext_I = self.params["external_input_exc"]
        noise_std = self.params["noise_std"]
        
        # Time integration
        for t in range(1, num_steps):
            # Noise term
            noise_E = self.rng.normal(0, noise_std, num_nodes)
            noise_I = self.rng.normal(0, noise_std, num_nodes)
            
            # Wilson-Cowan equations
            dE = (1.0 / tau_E) * (
                -E[:, t-1] + self._sigmoid(J @ E[:, t-1] - W @ I[:, t-1] + I_ext_E + noise_E, 1.0)
            )
            dI = (1.0 / tau_I) * (
                -I[:, t-1] + self._sigmoid(J @ E[:, t-1] - W @ I[:, t-1] + I_ext_I + noise_I, 1.0)
            )
            
            E[:, t] = E[:, t-1] + dt * dE
            I[:, t] = I[:, t-1] + dt * dI
        
        # Return excitatory activity as proxy for BOLD/EEG signal
        return E

def load_connectome(subject_id: str, data_root: Path) -> np.ndarray:
    """
    Load preprocessed connectome matrix for a subject.
    """
    store_path = data_root / "processed" / "connectomes"
    file_path = store_path / f"{subject_id}_connectome.npy"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Connectome not found for subject {subject_id} at {file_path}")
    
    return np.load(file_path)

def simulate_eeg_for_subject(
    subject_id: str,
    data_root: Path,
    params: Optional[Dict[str, Any]] = None,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Simulate EEG time-series for a single subject and save metadata.
    
    This function implements the primary path for data generation when real EEG is unavailable.
    It logs the random seed and Wilson-Cowan parameters to ensure reproducibility.
    """
    if seed is None:
        seed = get_simulation_seed()
    
    logger.info(f"Starting EEG simulation for subject {subject_id} with seed {seed}")
    
    # Initialize simulator
    simulator = WilsonCowanSimulator(params=params, seed=seed)
    
    # Load connectome
    try:
        connectivity_matrix = load_connectome(subject_id, data_root)
        num_nodes = connectivity_matrix.shape[0]
    except FileNotFoundError as e:
        logger.error(f"Failed to load connectome for {subject_id}: {e}")
        raise SimulationError(f"Cannot simulate EEG: missing connectome for {subject_id}") from e
    
    # Run simulation
    raw_activity = simulator.simulate(connectivity_matrix, num_nodes)
    
    # Downsample to 250 Hz (if simulation rate was higher)
    # Assuming simulation was at 1/dt Hz
    sim_rate = 1.0 / simulator.params["dt"]
    if sim_rate > simulator.params["sampling_rate"]:
        # Simple decimation for demonstration; in production use scipy.signal.decimate
        factor = int(sim_rate / simulator.params["sampling_rate"])
        downsampled_activity = raw_activity[:, ::factor]
        final_rate = sim_rate // factor
    else:
        downsampled_activity = raw_activity
        final_rate = sim_rate
    
    # Apply band-pass filter (1-40 Hz) using MNE
    # Create MNE Info object
    info = mne.create_info(ch_names=[f"Node_{i}" for i in range(num_nodes)], sfreq=final_rate, ch_types='eeg')
    raw_data = mne.io.RawArray(downsampled_activity.astype(np.float64), info)
    
    # Filter
    raw_data.filter(l_freq=1.0, h_freq=40.0, method='fir', verbose=False)
    
    # Extract filtered data
    filtered_data = raw_data.get_data()
    
    # Save simulated EEG to processed storage
    output_dir = data_root / "processed" / "eeg"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{subject_id}_simulated_eeg.npy"
    np.save(output_file, filtered_data)
    
    # --- REPRODUCTION LOGIC FOR T030 ---
    # Log and save simulation parameters to metadata file
    metadata_entry = {
        "subject_id": subject_id,
        "timestamp": datetime.utcnow().isoformat(),
        "random_seed": seed,
        "wilson_cowan_params": simulator.params,
        "simulation_rate": sim_rate,
        "final_sampling_rate": final_rate,
        "num_nodes": num_nodes,
        "num_timepoints": filtered_data.shape[1],
        "source_file": str(output_file),
        "params_hash": hashlib.sha256(json.dumps(simulator.params, sort_keys=True).encode()).hexdigest()
    }
    
    metadata_path = data_root / "processed" / "simulation_metadata.json"
    
    # Load existing metadata if it exists
    all_metadata = []
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r') as f:
                all_metadata = json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Existing metadata file {metadata_path} is corrupted. Overwriting.")
            all_metadata = []
    
    # Append new entry
    all_metadata.append(metadata_entry)
    
    # Write back
    with open(metadata_path, 'w') as f:
        json.dump(all_metadata, f, indent=2)
    
    logger.info(f"Simulation complete for {subject_id}. Metadata saved to {metadata_path}")
    logger.debug(f"Parameters used: {simulator.params}")
    
    return {
        "subject_id": subject_id,
        "output_file": str(output_file),
        "metadata_file": str(metadata_path),
        "shape": filtered_data.shape,
        "seed": seed
    }

def run_pipeline(subject_ids: List[str], data_root: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Run simulation pipeline for a list of subjects.
    """
    if data_root is None:
        data_root = get_data_root()
    
    ensure_directories(data_root)
    
    results = []
    for subject_id in subject_ids:
        try:
            result = simulate_eeg_for_subject(subject_id, data_root)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to simulate EEG for {subject_id}: {e}")
            # Continue processing other subjects
            results.append({"subject_id": subject_id, "error": str(e)})
    
    return results

@handle_exceptions
def main():
    """
    Entry point for the simulation script.
    """
    log_pipeline_start("simulate_EEG")
    
    # Get subject IDs from config or command line (simplified for this task)
    # In a real scenario, this would read from a manifest or config
    data_root = get_data_root()
    
    # Example: If we had a list of subjects from T009/T010
    # For now, we assume the caller passes the list or it's derived from existing files
    # We will scan the processed connectomes directory to find subjects
    connectome_dir = data_root / "processed" / "connectomes"
    if not connectome_dir.exists():
        logger.error("Connectome directory not found. Run preprocess_dMRI first.")
        sys.exit(1)
    
    subject_ids = [f.stem.replace("_connectome", "") for f in connectome_dir.glob("*_connectome.npy")]
    
    if not subject_ids:
        logger.warning("No subjects found in connectome directory.")
        sys.exit(0)
    
    logger.info(f"Found {len(subject_ids)} subjects to simulate.")
    
    results = run_pipeline(subject_ids, data_root)
    
    # Summary
    successful = sum(1 for r in results if "error" not in r)
    logger.info(f"Simulation pipeline complete. {successful}/{len(subject_ids)} successful.")
    
    log_pipeline_end("simulate_EEG")
    return results

if __name__ == "__main__":
    main()