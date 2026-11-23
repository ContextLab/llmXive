"""
Synthetic MD trajectory generation for amorphous solids under shear stress.

This module generates synthetic molecular dynamics trajectories with:
- Particle coordinates (x, y, z)
- Box dimensions (Lx, Ly, Lz)
- Stress tensors (3x3)
- Labels: "brittle" or "ductile" based on physical parameters

Outputs:
- data/raw/synthetic_trajectory_*.h5
- data/raw/metadata.json
"""

import os
import json
import h5py
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Import seed from utils to ensure reproducibility
from utils import set_seed

# Constants
DEFAULT_NUM_PARTICLES = 1000
DEFAULT_NUM_TIMESTEPS = 500
DEFAULT_BOX_SIZE = 20.0  # Angstroms
DEFAULT_TEMPERATURE = 300.0  # Kelvin
DEFAULT_STRAIN_RATE = 1e-8  # 1/s
DEFAULT_DENSITY = 2.3  # g/cm^3 for amorphous silicon

# Output paths
OUTPUT_DIR = Path("data/raw")
METADATA_PATH = OUTPUT_DIR / "metadata.json"

def _compute_box_dimensions(num_particles: int, density: float) -> Tuple[float, float, float]:
    """
    Compute cubic box dimensions based on particle count and density.
    For amorphous silicon (density ~2.3 g/cm^3, atomic mass ~28.0855 g/mol)
    """
    # Volume in cm^3
    molar_mass = 28.0855  # g/mol for Silicon
    avogadro = 6.022e23
    volume_cm3 = (num_particles * molar_mass) / (density * avogadro)
    volume_angstrom3 = volume_cm3 * (1e8) ** 3
    
    # Cubic box
    L = volume_angstrom3 ** (1/3)
    return L, L, L

def _generate_initial_coordinates(num_particles: int, Lx: float, Ly: float, Lz: float) -> np.ndarray:
    """
    Generate random initial coordinates within the box.
    Uses a simple random distribution with minimum separation check.
    """
    coords = np.random.uniform(0, 1, size=(num_particles, 3))
    coords[:, 0] *= Lx
    coords[:, 1] *= Ly
    coords[:, 2] *= Lz
    return coords

def _apply_shear_deformation(coords: np.ndarray, timestep: int, strain_rate: float, 
                             Lx: float, Ly: float, Lz: float) -> np.ndarray:
    """
    Apply simple shear deformation in x-direction as a function of y-coordinate.
    gamma = strain_rate * timestep
    x' = x + gamma * y
    """
    gamma = strain_rate * timestep
    new_coords = coords.copy()
    new_coords[:, 0] = (coords[:, 0] + gamma * coords[:, 1]) % Lx
    return new_coords

def _compute_stress_tensor(coords: np.ndarray, prev_coords: np.ndarray, 
                          timestep: int, temperature: float, 
                          strain_rate: float, is_brittle: bool) -> np.ndarray:
    """
    Compute a simplified stress tensor based on deformation.
    
    For brittle materials: High initial stress, sharp drop at yield
    For ductile materials: Lower initial stress, gradual plastic flow
    
    Returns a 3x3 stress tensor (units: arbitrary stress units)
    """
    # Calculate strain
    gamma = strain_rate * timestep
    
    # Base stress magnitude
    base_stress = 10.0  # arbitrary units
    
    if is_brittle:
        # Brittle: High stress, sharp drop after yield point (~50% of simulation)
        yield_point = 0.5 * len(coords)  # Simplified yield point
        if timestep < yield_point:
            stress_xy = base_stress * (1 - 0.001 * timestep)
        else:
            # Sharp drop
            stress_xy = base_stress * 0.2 * np.exp(-0.1 * (timestep - yield_point))
    else:
        # Ductile: Lower stress, gradual increase then plateau
        stress_xy = base_stress * 0.6 * (1 - np.exp(-0.01 * timestep))
    
    # Construct stress tensor (simplified, only shear component significant)
    stress = np.zeros((3, 3))
    stress[0, 1] = stress_xy
    stress[1, 0] = stress_xy
    
    # Add some thermal noise
    noise_scale = temperature * 0.01
    stress += np.random.normal(0, noise_scale, (3, 3))
    
    # Ensure symmetry
    stress = (stress + stress.T) / 2.0
    
    return stress

def _determine_label(strain_rate: float, temperature: float) -> str:
    """
    Determine if the trajectory should be labeled 'brittle' or 'ductile'
    based on physical simulation parameters.
    
    Heuristic:
    - High strain rate + Low temperature -> Brittle
    - Low strain rate + High temperature -> Ductile
    """
    # Normalize parameters (approximate ranges)
    high_strain_rate = strain_rate > 1e-7
    low_temperature = temperature < 400.0
    
    if high_strain_rate and low_temperature:
        return "brittle"
    else:
        return "ductile"

def generate_synthetic_trajectory(num_particles: int = DEFAULT_NUM_PARTICLES,
                                  num_timesteps: int = DEFAULT_NUM_TIMESTEPS,
                                  temperature: float = DEFAULT_TEMPERATURE,
                                  strain_rate: float = DEFAULT_STRAIN_RATE,
                                  seed: int = 42) -> Dict:
    """
    Generate a complete synthetic MD trajectory.
    
    Args:
        num_particles: Number of particles in the system
        num_timesteps: Number of timesteps to simulate
        temperature: System temperature in Kelvin
        strain_rate: Applied strain rate (1/s)
        seed: Random seed for reproducibility
    
    Returns:
        Dictionary containing:
            - particles: Array of coordinates (timesteps x particles x 3)
            - box_dimensions: (Lx, Ly, Lz)
            - stress_tensor: Array of stress tensors (timesteps x 3 x 3)
            - label: 'brittle' or 'ductile'
            - metadata: Simulation parameters
    """
    set_seed(seed)
    
    # Compute box dimensions
    Lx, Ly, Lz = _compute_box_dimensions(num_particles, DEFAULT_DENSITY)
    box_dims = {"Lx": Lx, "Ly": Ly, "Lz": Lz}
    
    # Determine label based on parameters
    label = _determine_label(strain_rate, temperature)
    
    # Generate initial coordinates
    coords = _generate_initial_coordinates(num_particles, Lx, Ly, Lz)
    
    # Arrays to store trajectory data
    all_coords = np.zeros((num_timesteps, num_particles, 3))
    all_stress = np.zeros((num_timesteps, 3, 3))
    
    # Simulate timesteps
    prev_coords = coords.copy()
    for t in range(num_timesteps):
        # Apply shear deformation
        coords = _apply_shear_deformation(coords, t, strain_rate, Lx, Ly, Lz)
        all_coords[t] = coords
        
        # Compute stress tensor
        stress = _compute_stress_tensor(coords, prev_coords, t, temperature, strain_rate, label == "brittle")
        all_stress[t] = stress
        
        prev_coords = coords.copy()
    
    return {
        "particles": all_coords,
        "box_dimensions": box_dims,
        "stress_tensor": all_stress,
        "timesteps": num_timesteps,
        "label": label,
        "metadata": {
            "num_particles": num_particles,
            "num_timesteps": num_timesteps,
            "temperature": temperature,
            "strain_rate": strain_rate,
            "density": DEFAULT_DENSITY,
            "seed": seed,
            "source": "synthetic_generator"
        }
    }

def save_trajectory_to_h5(trajectory_data: Dict, output_path: str) -> None:
    """
    Save trajectory data to an HDF5 file.
    
    Args:
        trajectory_data: Dictionary from generate_synthetic_trajectory
        output_path: Path to save the HDF5 file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with h5py.File(output_path, 'w') as f:
        # Save particles
        f.create_dataset('particles', data=trajectory_data['particles'])
        
        # Save box dimensions
        box_group = f.create_group('box_dimensions')
        box_group.create_dataset('Lx', data=trajectory_data['box_dimensions']['Lx'])
        box_group.create_dataset('Ly', data=trajectory_data['box_dimensions']['Ly'])
        box_group.create_dataset('Lz', data=trajectory_data['box_dimensions']['Lz'])
        
        # Save stress tensor
        f.create_dataset('stress_tensor', data=trajectory_data['stress_tensor'])
        
        # Save metadata
        f.attrs['timesteps'] = trajectory_data['timesteps']
        f.attrs['label'] = trajectory_data['label']
        
        # Save metadata dict as JSON string
        f.attrs['metadata_json'] = json.dumps(trajectory_data['metadata'])

def save_metadata_json(all_trajectories: List[Dict]) -> None:
    """
    Save aggregated metadata for all generated trajectories.
    
    Args:
        all_trajectories: List of trajectory data dictionaries
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    metadata_list = []
    for i, traj in enumerate(all_trajectories):
        entry = {
            "filename": f"synthetic_trajectory_{i}.h5",
            "label": traj['label'],
            "num_particles": traj['metadata']['num_particles'],
            "num_timesteps": traj['metadata']['num_timesteps'],
            "temperature": traj['metadata']['temperature'],
            "strain_rate": traj['metadata']['strain_rate'],
            "seed": traj['metadata']['seed']
        }
        metadata_list.append(entry)
    
    with open(METADATA_PATH, 'w') as f:
        json.dump(metadata_list, f, indent=2)

def main():
    """
    Main entry point to generate synthetic trajectories.
    Generates multiple trajectories with varying parameters to create
    a balanced dataset of brittle and ductile samples.
    """
    print("Starting synthetic trajectory generation...")
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Define parameter combinations to generate diverse dataset
    # Aim for roughly equal brittle/ductile samples
    params = [
        # Brittle conditions (high strain rate, low temp)
        {"num_particles": 1000, "num_timesteps": 500, "temperature": 300.0, "strain_rate": 1e-6, "seed": 42},
        {"num_particles": 1000, "num_timesteps": 500, "temperature": 250.0, "strain_rate": 5e-7, "seed": 43},
        {"num_particles": 1000, "num_timesteps": 500, "temperature": 350.0, "strain_rate": 2e-6, "seed": 44},
        {"num_particles": 1000, "num_timesteps": 500, "temperature": 280.0, "strain_rate": 8e-7, "seed": 45},
        {"num_particles": 1000, "num_timesteps": 500, "temperature": 320.0, "strain_rate": 1.5e-6, "seed": 46},
        
        # Ductile conditions (low strain rate, high temp)
        {"num_particles": 1000, "num_timesteps": 500, "temperature": 500.0, "strain_rate": 1e-9, "seed": 47},
        {"num_particles": 1000, "num_timesteps": 500, "temperature": 450.0, "strain_rate": 5e-10, "seed": 48},
        {"num_particles": 1000, "num_timesteps": 500, "temperature": 600.0, "strain_rate": 2e-9, "seed": 49},
        {"num_particles": 1000, "num_timesteps": 500, "temperature": 480.0, "strain_rate": 8e-10, "seed": 50},
        {"num_particles": 1000, "num_timesteps": 500, "temperature": 550.0, "strain_rate": 1.5e-9, "seed": 51},
    ]
    
    all_trajectories = []
    
    for i, p in enumerate(params):
        print(f"Generating trajectory {i+1}/{len(params)}...")
        traj_data = generate_synthetic_trajectory(
            num_particles=p["num_particles"],
            num_timesteps=p["num_timesteps"],
            temperature=p["temperature"],
            strain_rate=p["strain_rate"],
            seed=p["seed"]
        )
        
        output_file = OUTPUT_DIR / f"synthetic_trajectory_{i}.h5"
        save_trajectory_to_h5(traj_data, str(output_file))
        all_trajectories.append(traj_data)
        print(f"  Saved: {output_file} (Label: {traj_data['label']})")
    
    # Save aggregated metadata
    save_metadata_json(all_trajectories)
    print(f"Saved metadata to {METADATA_PATH}")
    
    # Summary
    brittle_count = sum(1 for t in all_trajectories if t['label'] == 'brittle')
    ductile_count = len(all_trajectories) - brittle_count
    print(f"\nGeneration complete!")
    print(f"  Total trajectories: {len(all_trajectories)}")
    print(f"  Brittle: {brittle_count}")
    print(f"  Ductile: {ductile_count}")
    print(f"  Output directory: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
