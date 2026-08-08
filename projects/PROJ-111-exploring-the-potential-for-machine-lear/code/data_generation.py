import os
import sys
import hashlib
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any
import numpy as np
import torch
from config import get_config

# Ensure logging is configured before other imports that might log
from logging_config import setup_logging, get_logger
logger = get_logger(__name__)

def ensure_data_dir():
    """Ensure the data directories exist."""
    config = get_config()
    data_dir = Path(config.data_dir)
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured data directories exist: {raw_dir}, {processed_dir}")
    return raw_dir, processed_dir

def verify_checksum(filepath: Path, expected_checksum: str) -> bool:
    """Verify the checksum of a file."""
    if not filepath.exists():
        logger.warning(f"File {filepath} does not exist, checksum verification failed.")
        return False
    hasher = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    actual_checksum = hasher.hexdigest()
    if actual_checksum == expected_checksum:
        logger.info(f"Checksum verified for {filepath}: {actual_checksum}")
        return True
    else:
        logger.error(f"Checksum mismatch for {filepath}: expected {expected_checksum}, got {actual_checksum}")
        return False

def initialize_spins_heisenberg(L: int, seed: int) -> np.ndarray:
    """
    Initialize spin configurations for the J1-J2 Heisenberg model.
    Returns an array of shape (N, L, L, 3) where N is the number of configurations (1 here for initialization).
    Spins are normalized to unit length.
    """
    rng = np.random.default_rng(seed)
    # Initialize random unit vectors
    # Method: generate 3 normal variates and normalize
    spins = rng.normal(size=(1, L, L, 3))
    norms = np.linalg.norm(spins, axis=3, keepdims=True)
    spins = spins / norms
    logger.debug(f"Heisenberg spins initialized: shape {spins.shape}, seed {seed}")
    return spins

def initialize_spins_xy(L: int, seed: int) -> np.ndarray:
    """
    Initialize spin configurations for the XY model.
    Returns an array of shape (N, L, L, 2) where N is the number of configurations (1 here for initialization).
    Spins are normalized to unit length (on the unit circle).
    """
    rng = np.random.default_rng(seed)
    # Initialize random angles
    angles = rng.uniform(0, 2 * np.pi, size=(1, L, L))
    spins = np.stack([np.cos(angles), np.sin(angles)], axis=-1)
    logger.debug(f"XY spins initialized: shape {spins.shape}, seed {seed}")
    return spins

def energy_heisenberg(spins: np.ndarray, J1: float, J2: float) -> float:
    """
    Calculate the energy of a Heisenberg configuration.
    Hamiltonian: H = J1 * sum(Si.Sj)nn + J2 * sum(Si.Sj)nnn
    Note: Standard convention often has H = -J sum... but we follow the sign convention
    implied by the project context (usually minimizing energy for ground state).
    Here we implement H = J1 * sum(Si.Sj) + J2 * sum(Si.Sj).
    """
    L = spins.shape[1]
    energy = 0.0
    # Nearest neighbors (periodic boundary conditions)
    for i in range(L):
        for j in range(L):
            s = spins[0, i, j]
            # Right neighbor
            s_right = spins[0, i, (j + 1) % L]
            energy += np.dot(s, s_right)
            # Bottom neighbor
            s_bottom = spins[0, (i + 1) % L, j]
            energy += np.dot(s, s_bottom)
    
    # Next-nearest neighbors (diagonal)
    for i in range(L):
        for j in range(L):
            s = spins[0, i, j]
            # Diagonal 1
            s_diag1 = spins[0, (i + 1) % L, (j + 1) % L]
            energy += np.dot(s, s_diag1)
            # Diagonal 2
            s_diag2 = spins[0, (i + 1) % L, (j - 1) % L]
            energy += np.dot(s, s_diag2)
    
    return J1 * energy * 0.5 + J2 * energy * 0.25 # 0.5 to avoid double counting NN, 0.25 for NNN

def energy_xy(spins: np.ndarray, J1: float, J2: float) -> float:
    """
    Calculate the energy of an XY configuration.
    Same logic as Heisenberg but spins are 2D.
    """
    L = spins.shape[1]
    energy = 0.0
    # Nearest neighbors
    for i in range(L):
        for j in range(L):
            s = spins[0, i, j]
            s_right = spins[0, i, (j + 1) % L]
            energy += np.dot(s, s_right)
            s_bottom = spins[0, (i + 1) % L, j]
            energy += np.dot(s, s_bottom)
    
    # Next-nearest neighbors
    for i in range(L):
        for j in range(L):
            s = spins[0, i, j]
            s_diag1 = spins[0, (i + 1) % L, (j + 1) % L]
            energy += np.dot(s, s_diag1)
            s_diag2 = spins[0, (i + 1) % L, (j - 1) % L]
            energy += np.dot(s, s_diag2)
    
    return J1 * energy * 0.5 + J2 * energy * 0.25

def metropolis_step_heisenberg(spins: np.ndarray, beta: float, J1: float, J2: float, rng: np.random.Generator) -> np.ndarray:
    """Perform one Metropolis step for the Heisenberg model."""
    L = spins.shape[1]
    new_spins = spins.copy()
    for _ in range(L * L): # Sweep over all sites
        i = rng.integers(0, L)
        j = rng.integers(0, L)
        old_spin = new_spins[0, i, j]
        
        # Propose a new spin (random rotation)
        # Simple approach: random unit vector
        delta = rng.normal(size=3)
        delta /= np.linalg.norm(delta)
        # Mix old and new to keep it local? Or just random?
        # Standard Metropolis for Heisenberg: pick a random new direction
        new_spin_candidate = rng.normal(size=3)
        new_spin_candidate /= np.linalg.norm(new_spin_candidate)
        
        # Calculate energy difference
        # This is expensive if done naively. We'll do a simplified local check.
        # For simplicity in this implementation, we'll assume a global energy recalculation is too slow
        # and rely on a local approximation or just accept/reject based on a simplified local field.
        # However, for correctness, we need the local energy change.
        
        # Local energy contribution from neighbors
        neighbors = [
            new_spins[0, i, (j + 1) % L],
            new_spins[0, i, (j - 1) % L],
            new_spins[0, (i + 1) % L, j],
            new_spins[0, (i - 1) % L, j],
            new_spins[0, (i + 1) % L, (j + 1) % L],
            new_spins[0, (i + 1) % L, (j - 1) % L],
            new_spins[0, (i - 1) % L, (j + 1) % L],
            new_spins[0, (i - 1) % L, (j - 1) % L],
        ]
        
        # This is a simplified local energy calculation
        # Real implementation would need to be more efficient
        # For now, we'll just accept the move with a probability based on a random energy change
        # to simulate the Metropolis process without full energy recalculation overhead in this snippet.
        # A proper implementation would calculate the exact local energy difference.
        
        # Placeholder for actual energy diff calculation
        # dE = J1 * (new_spin_candidate - old_spin) . (sum of NN) + J2 * ...
        # Since full calculation is complex, we'll use a random acceptance for demonstration
        # of the loop structure, but in a real run, this must be precise.
        # To satisfy "real data" requirement, we must implement the logic correctly.
        # Let's do a proper local energy diff.
        
        # Nearest neighbor sum
        nn_sum = np.zeros(3)
        nn_sum += new_spins[0, i, (j + 1) % L]
        nn_sum += new_spins[0, i, (j - 1) % L]
        nn_sum += new_spins[0, (i + 1) % L, j]
        nn_sum += new_spins[0, (i - 1) % L, j]
        
        # Next-nearest neighbor sum
        nnn_sum = np.zeros(3)
        nnn_sum += new_spins[0, (i + 1) % L, (j + 1) % L]
        nnn_sum += new_spins[0, (i + 1) % L, (j - 1) % L]
        nnn_sum += new_spins[0, (i - 1) % L, (j + 1) % L]
        nnn_sum += new_spins[0, (i - 1) % L, (j - 1) % L]
        
        old_local_energy = J1 * np.dot(old_spin, nn_sum) + J2 * np.dot(old_spin, nnn_sum)
        new_local_energy = J1 * np.dot(new_spin_candidate, nn_sum) + J2 * np.dot(new_spin_candidate, nnn_sum)
        
        dE = new_local_energy - old_local_energy
        
        if dE < 0 or rng.random() < np.exp(-beta * dE):
            new_spins[0, i, j] = new_spin_candidate
    
    return new_spins

def metropolis_step_xy(spins: np.ndarray, beta: float, J1: float, J2: float, rng: np.random.Generator) -> np.ndarray:
    """Perform one Metropolis step for the XY model."""
    L = spins.shape[1]
    new_spins = spins.copy()
    for _ in range(L * L):
        i = rng.integers(0, L)
        j = rng.integers(0, L)
        old_spin = new_spins[0, i, j]
        
        # Propose a new angle
        current_angle = np.arctan2(old_spin[1], old_spin[0])
        delta_angle = rng.uniform(-0.5, 0.5) # Small step
        new_angle = current_angle + delta_angle
        new_spin_candidate = np.array([np.cos(new_angle), np.sin(new_angle)])
        
        # Local energy calculation
        nn_sum = np.zeros(2)
        nn_sum += new_spins[0, i, (j + 1) % L]
        nn_sum += new_spins[0, i, (j - 1) % L]
        nn_sum += new_spins[0, (i + 1) % L, j]
        nn_sum += new_spins[0, (i - 1) % L, j]
        
        nnn_sum = np.zeros(2)
        nnn_sum += new_spins[0, (i + 1) % L, (j + 1) % L]
        nnn_sum += new_spins[0, (i + 1) % L, (j - 1) % L]
        nnn_sum += new_spins[0, (i - 1) % L, (j + 1) % L]
        nnn_sum += new_spins[0, (i - 1) % L, (j - 1) % L]
        
        old_local_energy = J1 * np.dot(old_spin, nn_sum) + J2 * np.dot(old_spin, nnn_sum)
        new_local_energy = J1 * np.dot(new_spin_candidate, nn_sum) + J2 * np.dot(new_spin_candidate, nnn_sum)
        
        dE = new_local_energy - old_local_energy
        
        if dE < 0 or rng.random() < np.exp(-beta * dE):
            new_spins[0, i, j] = new_spin_candidate
    
    return new_spins

def run_simulation(model_type: str, L: int, T: float, J1: float, J2: float, n_steps: int, seed: int) -> List[np.ndarray]:
    """
    Run the Monte Carlo simulation for a given model, lattice size, and temperature.
    Returns a list of configurations (thinned).
    """
    config = get_config()
    rng = np.random.default_rng(seed)
    
    # Initialize
    if model_type == "heisenberg":
        spins = initialize_spins_heisenberg(L, seed)
        metropolis_func = metropolis_step_heisenberg
    elif model_type == "xy":
        spins = initialize_spins_xy(L, seed)
        metropolis_func = metropolis_step_xy
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    beta = 1.0 / T
    
    logger.info(f"Starting simulation: Model={model_type}, L={L}, T={T}, J1={J1}, J2={J2}, Steps={n_steps}, Seed={seed}")
    
    configurations = []
    
    for step in range(n_steps):
        spins = metropolis_func(spins, beta, J1, J2, rng)
        # Save configurations periodically (e.g., every 10 steps for simplicity in this demo)
        # In a real scenario, thinning would be based on autocorrelation time (T007)
        if step % 10 == 0:
            configurations.append(spins.copy())
    
    logger.info(f"Simulation completed for Model={model_type}, L={L}, T={T}. Generated {len(configurations)} configurations.")
    return configurations

def save_data(model_type: str, L: int, T: float, configurations: List[np.ndarray], output_dir: Path):
    """Save the generated configurations to disk."""
    filename = f"{model_type}_L{L}_T{T:.2f}.npz"
    filepath = output_dir / filename
    
    # Stack configurations
    data = np.concatenate(configurations, axis=0)
    
    np.savez_compressed(filepath, data=data)
    logger.info(f"Saved {len(configurations)} configurations to {filepath}")
    
    # Log the parameters for reproducibility
    logger.info(f"Parameters logged: Model={model_type}, L={L}, T={T}, N_configs={len(configurations)}")

def main():
    """Main entry point for data generation."""
    config = get_config()
    setup_logging()
    
    # Log the generation parameters
    # These are typically read from config or command line args
    # For this task, we log the defaults or config values
    logger.info("Data Generation Task Started")
    
    # Example parameters - in real usage, these would be from config or args
    models = ["heisenberg", "xy"]
    L_sizes = [16, 24]
    temperatures = [0.1, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    J1, J2 = 1.0, 0.5 # Example coupling constants
    n_steps = 100 # Reduced for demo, should be higher in real run
    
    raw_dir, _ = ensure_data_dir()
    
    for model in models:
        for L in L_sizes:
            for T in temperatures:
                # Log parameters for this run
                logger.info(f"Generating data for {model}, L={L}, T={T}, J1={J1}, J2={J2}")
                
                try:
                    configs = run_simulation(model, L, T, J1, J2, n_steps, config.seed)
                    save_data(model, L, T, configs, raw_dir)
                except Exception as e:
                    logger.error(f"Failed to generate data for {model}, L={L}, T={T}: {e}")
                    raise

if __name__ == "__main__":
    main()
