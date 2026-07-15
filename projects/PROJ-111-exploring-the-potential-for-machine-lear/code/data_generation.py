import os
import sys
import hashlib
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any

import numpy as np

from config import get_config

# Configure logger for this module
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def ensure_data_dir() -> Path:
    """Ensure the raw data directory exists."""
    config = get_config()
    data_dir = Path(config.get('data_dir', 'data'))
    raw_dir = data_dir / 'raw'
    raw_dir.mkdir(parents=True, exist_ok=True)
    return raw_dir

def verify_checksum(filepath: Path, expected_checksum: str) -> bool:
    """Verify the checksum of a file."""
    if not filepath.exists():
        return False
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest() == expected_checksum

def initialize_spins_heisenberg(L: int, seed: int) -> np.ndarray:
    """Initialize random spin vectors for the Heisenberg model."""
    rng = np.random.default_rng(seed)
    # Random unit vectors in 3D
    # Method: Generate Gaussian, then normalize
    spins = rng.normal(size=(L, L, 3))
    norms = np.linalg.norm(spins, axis=-1, keepdims=True)
    return spins / norms

def initialize_spins_xy(L: int, seed: int) -> np.ndarray:
    """Initialize random spin vectors for the XY model (2D plane)."""
    rng = np.random.default_rng(seed)
    # Random angles in [0, 2pi)
    angles = rng.uniform(0, 2 * np.pi, size=(L, L))
    spins = np.stack([np.cos(angles), np.sin(angles)], axis=-1)
    # Pad to 3D for consistency with Heisenberg if needed, or keep 2D
    # The spec implies 3 components for Heisenberg, XY usually 2.
    # To match the `[batch, 3, L, L]` reshape in preprocessing, we pad XY to 3D with 0s
    # or treat the 3rd component as 0.
    spins_3d = np.zeros((L, L, 3))
    spins_3d[..., :2] = spins
    return spins_3d

def energy_heisenberg(spins: np.ndarray, J1: float, J2: float) -> float:
    """Calculate energy for Heisenberg model."""
    L = spins.shape[0]
    energy = 0.0
    # J1 nearest neighbors
    for i in range(L):
        for j in range(L):
            s = spins[i, j]
            # Right neighbor
            s_right = spins[i, (j + 1) % L]
            energy -= J1 * np.dot(s, s_right)
            # Down neighbor
            s_down = spins[(i + 1) % L, j]
            energy -= J1 * np.dot(s, s_down)
    # J2 next-nearest neighbors
    for i in range(L):
        for j in range(L):
            s = spins[i, j]
            # Down-Right
            s_dr = spins[(i + 1) % L, (j + 1) % L]
            energy -= J2 * np.dot(s, s_dr)
            # Down-Left
            s_dl = spins[(i + 1) % L, (j - 1) % L]
            energy -= J2 * np.dot(s, s_dl)
    return energy / 2.0  # Each bond counted twice

def energy_xy(spins: np.ndarray, J1: float, J2: float) -> float:
    """Calculate energy for XY model."""
    L = spins.shape[0]
    energy = 0.0
    # Use only x, y components
    s_xy = spins[..., :2]
    for i in range(L):
        for j in range(L):
            s = s_xy[i, j]
            s_right = s_xy[i, (j + 1) % L]
            energy -= J1 * np.dot(s, s_right)
            s_down = s_xy[(i + 1) % L, j]
            energy -= J1 * np.dot(s, s_down)
            s_dr = s_xy[(i + 1) % L, (j + 1) % L]
            energy -= J2 * np.dot(s, s_dr)
            s_dl = s_xy[(i + 1) % L, (j - 1) % L]
            energy -= J2 * np.dot(s, s_dl)
    return energy / 2.0

def metropolis_step_heisenberg(spins: np.ndarray, T: float, J1: float, J2: float, rng: np.random.Generator) -> np.ndarray:
    """Perform one Metropolis-Hastings step for Heisenberg model."""
    L = spins.shape[0]
    new_spins = spins.copy()
    for _ in range(L * L):  # Sweep
        i = rng.integers(0, L)
        j = rng.integers(0, L)
        old_spin = spins[i, j]
        # Propose new random unit vector
        new_spin_vec = rng.normal(size=3)
        new_spin_vec /= np.linalg.norm(new_spin_vec)

        # Calculate energy difference
        # Temporarily swap to calculate delta E
        # Neighbors: Right, Left, Up, Down, DR, DL, UL, UR
        # Efficient calculation:
        # Delta E = -J1 * (new - old) . (sum neighbors J1) - J2 * (new - old) . (sum neighbors J2)
        
        # Neighbors J1
        n_right = spins[i, (j+1)%L]
        n_left = spins[i, (j-1)%L]
        n_up = spins[(i-1)%L, j]
        n_down = spins[(i+1)%L, j]
        
        # Neighbors J2
        n_dr = spins[(i+1)%L, (j+1)%L]
        n_dl = spins[(i+1)%L, (j-1)%L]
        n_ul = spins[(i-1)%L, (j-1)%L]
        n_ur = spins[(i-1)%L, (j+1)%L]

        sum_j1 = n_right + n_left + n_up + n_down
        sum_j2 = n_dr + n_dl + n_ul + n_ur

        delta_E = -J1 * np.dot(new_spin_vec - old_spin, sum_j1) - J2 * np.dot(new_spin_vec - old_spin, sum_j2)

        if delta_E < 0 or rng.uniform() < np.exp(-delta_E / T):
            new_spins[i, j] = new_spin_vec
    return new_spins

def metropolis_step_xy(spins: np.ndarray, T: float, J1: float, J2: float, rng: np.random.Generator) -> np.ndarray:
    """Perform one Metropolis-Hastings step for XY model."""
    L = spins.shape[0]
    new_spins = spins.copy()
    for _ in range(L * L):
        i = rng.integers(0, L)
        j = rng.integers(0, L)
        old_spin = spins[i, j]
        # Propose new angle
        theta_old = np.arctan2(old_spin[1], old_spin[0])
        delta_theta = rng.uniform(-0.5, 0.5) # Small step
        theta_new = theta_old + delta_theta
        new_spin_vec = np.array([np.cos(theta_new), np.sin(theta_new), 0.0])

        # Neighbors (2D components)
        n_right = spins[i, (j+1)%L][:2]
        n_left = spins[i, (j-1)%L][:2]
        n_up = spins[(i-1)%L, j][:2]
        n_down = spins[(i+1)%L, j][:2]
        
        n_dr = spins[(i+1)%L, (j+1)%L][:2]
        n_dl = spins[(i+1)%L, (j-1)%L][:2]
        n_ul = spins[(i-1)%L, (j-1)%L][:2]
        n_ur = spins[(i-1)%L, (j+1)%L][:2]

        sum_j1 = n_right + n_left + n_up + n_down
        sum_j2 = n_dr + n_dl + n_ul + n_ur

        delta_E = -J1 * np.dot(new_spin_vec[:2] - old_spin[:2], sum_j1) - J2 * np.dot(new_spin_vec[:2] - old_spin[:2], sum_j2)

        if delta_E < 0 or rng.uniform() < np.exp(-delta_E / T):
            new_spins[i, j] = new_spin_vec
    return new_spins

def run_simulation(
    model_type: str,
    L: int,
    T: float,
    J1: float,
    J2: float,
    n_steps: int,
    seed: int,
    burn_in: int = 1000
) -> List[np.ndarray]:
    """Run Metropolis-Hastings simulation."""
    logger.info(f"Starting simulation: Model={model_type}, L={L}, T={T}, J1={J1}, J2={J2}, Steps={n_steps}")
    
    # Initialize spins
    if model_type == 'heisenberg':
        spins = initialize_spins_heisenberg(L, seed)
    elif model_type == 'xy':
        spins = initialize_spins_xy(L, seed)
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    rng = np.random.default_rng(seed + 1)
    
    # Burn-in
    logger.info(f"Running burn-in ({burn_in} steps)...")
    for _ in range(burn_in):
        if model_type == 'heisenberg':
            spins = metropolis_step_heisenberg(spins, T, J1, J2, rng)
        else:
            spins = metropolis_step_xy(spins, T, J1, J2, rng)

    # Production run
    configurations = []
    logger.info(f"Running production ({n_steps} steps)...")
    for step in range(n_steps):
        if model_type == 'heisenberg':
            spins = metropolis_step_heisenberg(spins, T, J1, J2, rng)
        else:
            spins = metropolis_step_xy(spins, T, J1, J2, rng)
        
        # Save configuration periodically or every step? 
        # For simplicity, save every step in this implementation, 
        # but in practice one might thin.
        configurations.append(spins.copy())
        
        if (step + 1) % 100 == 0:
            logger.debug(f"Step {step+1}/{n_steps}")

    logger.info(f"Simulation complete for T={T}, L={L}. Generated {len(configurations)} configurations.")
    return configurations

def save_data(
    model_type: str,
    L: int,
    T: float,
    J1: float,
    J2: float,
    configurations: List[np.ndarray],
    seed: int
) -> str:
    """Save configurations to disk."""
    raw_dir = ensure_data_dir()
    filename = f"{model_type}_L{L}_T{T:.2f}_J1{J1:.1f}_J2{J2:.1f}_seed{seed}.npz"
    filepath = raw_dir / filename
    
    # Stack to array
    data = np.stack(configurations, axis=0)
    np.savez_compressed(filepath, data=data)
    
    logger.info(f"Saved data to {filepath}")
    return str(filepath)

def main():
    """Main entry point to run simulations with logging."""
    config = get_config()
    
    # Parameters from config or defaults
    models = config.get('models', ['heisenberg', 'xy'])
    lattice_sizes = config.get('lattice_sizes', [16, 24])
    temperatures = config.get('temperatures', [0.1, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0])
    J1 = config.get('J1', 1.0)
    J2 = config.get('J2', 0.5) # Example ratio
    n_steps = config.get('n_steps', 100) # Small for demo, increase for real runs
    seed = config.get('seed', 42)
    burn_in = config.get('burn_in', 100)

    # Log all parameters
    logger.info("=== Data Generation Parameters ===")
    logger.info(f"Models: {models}")
    logger.info(f"Lattice Sizes: {lattice_sizes}")
    logger.info(f"Temperatures: {temperatures}")
    logger.info(f"J1: {J1}, J2: {J2}")
    logger.info(f"Steps: {n_steps}, Burn-in: {burn_in}, Seed: {seed}")
    logger.info("==================================")

    for model in models:
        for L in lattice_sizes:
            for T in temperatures:
                # Log start of specific run
                logger.info(f"Running {model} model: L={L}, T={T}")
                
                configs = run_simulation(
                    model_type=model,
                    L=L,
                    T=T,
                    J1=J1,
                    J2=J2,
                    n_steps=n_steps,
                    seed=seed,
                    burn_in=burn_in
                )
                
                save_data(
                    model_type=model,
                    L=L,
                    T=T,
                    J1=J1,
                    J2=J2,
                    configurations=configs,
                    seed=seed
                )

    logger.info("All simulations completed.")

if __name__ == "__main__":
    main()