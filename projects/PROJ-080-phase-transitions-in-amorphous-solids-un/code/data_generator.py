"""
Synthetic MD trajectory generation for amorphous solids under shear stress.

Generates particle coordinates, box dimensions, stress tensors, and assigns
"brittle" or "ductile" labels based on physical simulation parameters.

Output:
  - data/raw/synthetic_trajectory_*.h5
  - data/raw/metadata.json
"""
import os
import json
import h5py
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

# Import SEED from utils as per API surface
from utils import set_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_synthetic_trajectory(
    n_particles: int = 1000,
    n_steps: int = 500,
    strain_rate: float = 1e-5,
    temperature: float = 300.0,
    seed: int = 42,
    output_path: Optional[Path] = None
) -> Dict[str, any]:
    """
    Generate a synthetic molecular dynamics trajectory.
    
    Args:
        n_particles: Number of particles in the system
        n_steps: Number of timesteps to simulate
        strain_rate: Applied shear strain rate (1/s)
        temperature: System temperature (K)
        seed: Random seed for reproducibility
        output_path: Path to write the HDF5 file (optional)
    
    Returns:
        Dictionary containing trajectory metadata and parameters
    """
    set_seed(seed)
    
    # Initialize box dimensions (cubic box)
    box_length = 10.0 * np.cbrt(n_particles)  # Approximate density
    box = np.array([
        [box_length, 0.0, 0.0],
        [0.0, box_length, 0.0],
        [0.0, 0.0, box_length]
    ])
    
    # Initialize particle positions (random uniform in box)
    positions = np.random.uniform(0, box_length, size=(n_particles, 3))
    
    # Initialize velocities from Maxwell-Boltzmann distribution
    velocity_scale = np.sqrt(temperature / 100.0)  # Simplified scaling
    velocities = np.random.normal(0, velocity_scale, size=(n_particles, 3))
    
    # Initialize stress tensor components (Voigt notation: xx, yy, zz, xy, xz, yz)
    # Start with near-zero stress
    stress = np.zeros((n_steps, 6))
    
    # Generate trajectory data
    trajectories = []
    for step in range(n_steps):
        # Apply shear deformation (simple shear in x-y plane)
        shear_strain = step * strain_rate
        
        # Update positions with shear
        # Simple shear: x' = x + gamma * y
        shear_matrix = np.eye(3)
        shear_matrix[0, 1] = shear_strain
        
        # Periodic boundary conditions
        positions = positions @ shear_matrix.T
        positions = positions % box_length
        
        # Update velocities (simplified thermalization)
        noise = np.random.normal(0, velocity_scale * 0.1, size=(n_particles, 3))
        velocities = velocities * 0.99 + noise
        
        # Compute stress tensor (simplified model)
        # Stress increases linearly with strain until yield point, then drops
        yield_point = int(n_steps * 0.6)  # Yield at 60% of simulation
        
        if step < yield_point:
            # Elastic regime: stress increases with strain
            stress[step, :] = strain_rate * step * np.array([1.0, 1.0, 0.5, 0.8, 0.0, 0.0])
            # Add thermal fluctuations
            stress[step, :] += np.random.normal(0, 0.05, size=6)
        else:
            # Plastic regime: stress drops and fluctuates around a lower value
            drop_factor = np.exp(-0.1 * (step - yield_point))
            base_stress = strain_rate * yield_point * np.array([0.3, 0.3, 0.15, 0.2, 0.0, 0.0])
            stress[step, :] = base_stress * drop_factor + np.random.normal(0, 0.1, size=6)
        
        # Store trajectory snapshot
        trajectories.append({
            'step': step,
            'positions': positions.copy(),
            'velocities': velocities.copy(),
            'stress': stress[step, :].copy(),
            'box': box.copy()
        })
    
    # Determine label based on simulation parameters
    # Brittle: high strain rate, low temperature -> sharp drop
    # Ductile: low strain rate, high temperature -> gradual flow
    if strain_rate > 5e-5 or temperature < 200.0:
        label = "brittle"
    else:
        label = "ductile"
    
    metadata = {
        'n_particles': n_particles,
        'n_steps': n_steps,
        'strain_rate': strain_rate,
        'temperature': temperature,
        'seed': seed,
        'label': label,
        'box_length': box_length,
        'yield_point_step': yield_point,
        'trajectory_file': None  # Will be filled after writing
    }
    
    # Write to HDF5 if output_path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with h5py.File(output_path, 'w') as f:
            f.attrs['n_particles'] = n_particles
            f.attrs['n_steps'] = n_steps
            f.attrs['strain_rate'] = strain_rate
            f.attrs['temperature'] = temperature
            f.attrs['seed'] = seed
            f.attrs['label'] = label
            f.attrs['box_length'] = box_length
            
            # Create datasets
            f.create_dataset('steps', data=[t['step'] for t in trajectories])
            
            # Stack positions and velocities
            all_positions = np.array([t['positions'] for t in trajectories])
            all_velocities = np.array([t['velocities'] for t in trajectories])
            all_stress = np.array([t['stress'] for t in trajectories])
            
            f.create_dataset('positions', data=all_positions)
            f.create_dataset('velocities', data=all_velocities)
            f.create_dataset('stress', data=all_stress)
            
            # Store box dimensions (constant)
            f.create_dataset('box', data=box)
        
        metadata['trajectory_file'] = str(output_path)
        logger.info(f"Written trajectory to {output_path}")
    
    return metadata

def main():
    """Main entry point for synthetic data generation."""
    logger.info("Starting synthetic MD trajectory generation...")
    
    # Create output directories
    raw_data_dir = Path("data/raw")
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate multiple trajectories with different parameters
    # to create a diverse dataset
    configs = [
        {'n_particles': 500, 'n_steps': 300, 'strain_rate': 1e-5, 'temperature': 300.0, 'seed': 42},
        {'n_particles': 500, 'n_steps': 300, 'strain_rate': 1e-4, 'temperature': 300.0, 'seed': 43},
        {'n_particles': 500, 'n_steps': 300, 'strain_rate': 1e-5, 'temperature': 150.0, 'seed': 44},
        {'n_particles': 500, 'n_steps': 300, 'strain_rate': 1e-4, 'temperature': 150.0, 'seed': 45},
        {'n_particles': 500, 'n_steps': 300, 'strain_rate': 5e-5, 'temperature': 400.0, 'seed': 46},
    ]
    
    all_metadata = []
    
    for i, config in enumerate(configs):
        logger.info(f"Generating trajectory {i+1}/{len(configs)}...")
        
        output_file = raw_data_dir / f"synthetic_trajectory_{i:03d}.h5"
        
        metadata = generate_synthetic_trajectory(
            n_particles=config['n_particles'],
            n_steps=config['n_steps'],
            strain_rate=config['strain_rate'],
            temperature=config['temperature'],
            seed=config['seed'],
            output_path=output_file
        )
        
        all_metadata.append(metadata)
    
    # Write combined metadata
    metadata_file = raw_data_dir / "metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump({
            'dataset_info': 'Synthetic MD trajectories for amorphous solids',
            'generation_timestamp': str(Path.cwd()),
            'trajectories': all_metadata
        }, f, indent=2)
    
    logger.info(f"All trajectories generated. Metadata written to {metadata_file}")
    logger.info("Synthetic data generation complete.")

if __name__ == "__main__":
    main()
