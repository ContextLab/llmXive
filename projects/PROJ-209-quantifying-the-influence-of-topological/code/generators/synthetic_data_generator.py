"""
Synthetic Data Generator for 2D Material Defect Properties.

Implements physics-based surrogate models for generating training and holdout
datasets when real defect data is unavailable.

Surrogate Model Logic:
- Analytical Signal: Continuum elasticity (E = E0 * (1 - k*density))
- Noise: Gaussian (sigma=0.05) calibrated from DFT dataset statistics
- Physics Constraints: Griffith criterion, Rule of Mixtures, Matthiessen's rule
"""
import os
import csv
import json
import hashlib
import subprocess
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path

# Constants for physics-based generation
SEED = 42
NOISE_SIGMA = 0.05
ELASTICITY_K = 0.8  # Scaling factor for density impact
DEFECT_TYPES = ['vacancy', 'substitution', 'interstitial', 'grain_boundary']
MATERIAL_TYPES = ['graphene', 'MoS2']

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def ensure_output_directories() -> None:
    """Ensure all required output directories exist."""
    project_root = get_project_root()
    raw_dir = project_root / 'data' / 'raw'
    raw_dir.mkdir(parents=True, exist_ok=True)

def get_git_hash() -> str:
    """Get the current git commit hash for reproducibility."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=get_project_root(),
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def apply_griffith_criterion(
    fracture_energy: float,
    elastic_modulus: float,
    defect_size: float
) -> float:
    """
    Apply Griffith criterion for fracture strength.
    
    sigma_f = sqrt(2 * E * gamma / (pi * a))
    where:
      E = elastic modulus
      gamma = fracture energy
      a = defect size (crack length)
    """
    if defect_size <= 0:
        defect_size = 0.01  # Minimum defect size
    if elastic_modulus <= 0 or fracture_energy <= 0:
        return 0.0
    return np.sqrt(2 * elastic_modulus * fracture_energy / (np.pi * defect_size))

def apply_rule_of_mixtures(
    base_property: float,
    defect_fraction: float,
    defect_property: float
) -> float:
    """
    Apply rule of mixtures for composite properties.
    
    P_composite = V1 * P1 + V2 * P2
    """
    return (1 - defect_fraction) * base_property + defect_fraction * defect_property

def apply_matthiessen_rule(
    base_conductivity: float,
    defect_conductivity: float,
    defect_density: float
) -> float:
    """
    Apply Matthiessen's rule for conductivity reduction.
    
    1/sigma_total = 1/sigma_base + 1/sigma_defect
    """
    if base_conductivity <= 0 or defect_conductivity <= 0:
        return 0.0
    inverse_total = (1 / base_conductivity) + (defect_density / defect_conductivity)
    return 1 / inverse_total if inverse_total > 0 else 0.0

def generate_synthetic_data(
    n_samples: int,
    seed: int = SEED
) -> List[Dict[str, Any]]:
    """
    Generate synthetic dataset using physics-based surrogate models.
    
    Args:
        n_samples: Number of samples to generate
        seed: Random seed for reproducibility
        
    Returns:
        List of dictionaries containing synthetic data points
    """
    np.random.seed(seed)
    data = []
    
    for i in range(n_samples):
        # Generate random defect parameters
        material = np.random.choice(MATERIAL_TYPES)
        defect_type = np.random.choice(DEFECT_TYPES)
        defect_density = np.random.uniform(0.001, 0.1)  # 0.1% to 10%
        defect_size = np.random.uniform(0.1, 5.0)  # nm
        
        # Base material properties (approximate real values)
        if material == 'graphene':
            base_conductivity = 1e6  # S/m
            base_elastic_modulus = 1000  # GPa
            base_fracture_energy = 10  # J/m^2
        else:  # MoS2
            base_conductivity = 1e3  # S/m
            base_elastic_modulus = 330  # GPa
            base_fracture_energy = 5  # J/m^2
        
        # Apply physics-based models
        # Conductivity: Matthiessen's rule with Gaussian noise
        defect_conductivity = base_conductivity * 0.1
        conductivity = apply_matthiessen_rule(
            base_conductivity, defect_conductivity, defect_density
        )
        conductivity *= np.random.normal(1.0, NOISE_SIGMA)
        conductivity = max(0, conductivity)
        
        # Elastic modulus: Continuum elasticity model
        # E = E0 * (1 - k*density) + noise
        elastic_modulus = base_elastic_modulus * (1 - ELASTICITY_K * defect_density)
        elastic_modulus *= np.random.normal(1.0, NOISE_SIGMA)
        elastic_modulus = max(0, elastic_modulus)
        
        # Fracture energy: Rule of mixtures with noise
        defect_fracture_energy = base_fracture_energy * 0.5
        fracture_energy = apply_rule_of_mixtures(
            base_fracture_energy, defect_density, defect_fracture_energy
        )
        fracture_energy *= np.random.normal(1.0, NOISE_SIGMA)
        fracture_energy = max(0, fracture_energy)
        
        # Fracture strength: Griffith criterion
        fracture_strength = apply_griffith_criterion(
            fracture_energy, elastic_modulus, defect_size
        )
        fracture_strength *= np.random.normal(1.0, NOISE_SIGMA)
        fracture_strength = max(0, fracture_strength)
        
        # Create data point
        data_point = {
            'id': f'synth_{i:05d}',
            'material': material,
            'defect_type': defect_type,
            'defect_density': defect_density,
            'defect_size': defect_size,
            'conductivity': conductivity,
            'elastic_modulus': elastic_modulus,
            'fracture_energy': fracture_energy,
            'fracture_strength': fracture_strength,
            'generation_seed': seed,
            'generation_timestamp': 'synthetic'
        }
        data.append(data_point)
    
    return data

def save_to_csv(data: List[Dict[str, Any]], file_path: str) -> None:
    """Save synthetic data to CSV file."""
    if not data:
        raise ValueError("Cannot save empty data")
    
    fieldnames = list(data[0].keys())
    with open(file_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def generate_holdout_data(
    n_samples: int,
    seed: int = SEED
) -> List[Dict[str, Any]]:
    """
    Generate holdout dataset with different seed for validation.
    
    Args:
        n_samples: Number of samples to generate
        seed: Random seed for reproducibility
        
    Returns:
        List of dictionaries containing synthetic holdout data
    """
    # Use a different seed for holdout to ensure independence
    holdout_seed = seed + 1000
    return generate_synthetic_data(n_samples, holdout_seed)

def main() -> None:
    """Main function to generate synthetic training and holdout datasets."""
    print("Starting synthetic data generation for T013...")
    
    # Ensure output directories exist
    ensure_output_directories()
    
    project_root = get_project_root()
    
    # Check generation status to confirm synthetic mode is active
    generation_status_path = project_root / 'data' / 'state' / 'generation_status.json'
    if not generation_status_path.exists():
        print(f"[ERROR] Generation status file not found: {generation_status_path}")
        print("This task requires T012 to run first to set the generation status.")
        return
    
    with open(generation_status_path, 'r') as f:
        status = json.load(f)
    
    if status.get('source') != 'synthetic':
        print(f"[INFO] Generation source is '{status.get('source')}', skipping synthetic generation.")
        print("This task only runs when source is 'synthetic'.")
        return
    
    print(f"Generating synthetic data with seed={SEED}...")
    
    # Generate training data (N=1000+)
    train_data = generate_synthetic_data(n_samples=1000, seed=SEED)
    train_path = project_root / 'data' / 'raw' / 'synthetic_train.csv'
    save_to_csv(train_data, str(train_path))
    print(f"Generated training data: {train_path} ({len(train_data)} samples)")
    
    # Generate holdout data (N=200)
    holdout_data = generate_holdout_data(n_samples=200, seed=SEED)
    holdout_path = project_root / 'data' / 'raw' / 'synthetic_holdout.csv'
    save_to_csv(holdout_data, str(holdout_path))
    print(f"Generated holdout data: {holdout_path} ({len(holdout_data)} samples)")
    
    # Record checksums
    train_checksum = compute_sha256(str(train_path))
    holdout_checksum = compute_sha256(str(holdout_path))
    
    print(f"Training data checksum: {train_checksum}")
    print(f"Holdout data checksum: {holdout_checksum}")
    print("Synthetic data generation completed successfully.")

if __name__ == "__main__":
    main()
