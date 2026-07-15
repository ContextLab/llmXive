import os
import csv
import json
import hashlib
import subprocess
import numpy as np
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Import from infrastructure
from infrastructure.path_utils import get_project_root, ensure_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_git_hash() -> str:
    """Retrieve the current git commit hash for versioning."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=get_project_root(),
            check=True
        )
        return result.stdout.decode('utf-8').strip()
    except Exception:
        return "unknown"

def ensure_output_directories() -> None:
    """Ensure all required output directories exist."""
    root = get_project_root()
    dirs = [
        root / 'data' / 'raw',
        root / 'data' / 'processed',
        root / 'data' / 'validation',
        root / 'figures',
        root / 'state' / 'projects'
    ]
    for d in dirs:
        ensure_dir(d)

def apply_griffith_criterion(density: float, base_strength: float = 1.0) -> float:
    """
    Apply Griffith criterion for fracture strength.
    Simplified model: strength decreases with defect density.
    """
    # Simplified physical model: sigma = sigma_0 * (1 - k * density)
    # k is a material constant, here assumed ~1.5 for demonstration
    k = 1.5
    strength = base_strength * (1 - k * density)
    return max(0.0, strength)  # Physical bound

def apply_rule_of_mixtures(density: float, base_modulus: float = 1.0) -> float:
    """
    Apply Rule of Mixtures for Young's Modulus.
    Simplified model: modulus decreases linearly with defect density.
    """
    # E = E_0 * (1 - alpha * density)
    alpha = 2.0  # Empirical factor
    modulus = base_modulus * (1 - alpha * density)
    return max(0.0, modulus)

def apply_matthiessen_rule(density: float, base_conductivity: float = 1.0) -> float:
    """
    Apply Matthiessen's rule for conductivity.
    Simplified model: conductivity decreases with defect density.
    """
    # sigma = sigma_0 / (1 + beta * density)
    beta = 3.0  # Empirical factor
    conductivity = base_conductivity / (1 + beta * density)
    return max(0.0, conductivity)

def generate_synthetic_data(
    output_path: str,
    min_entries: int = 100,
    defect_density_range: Tuple[float, float] = (0.001, 0.1),
    seed: int = 42,
    version: str = "unknown"
) -> str:
    """
    Generate synthetic defect dataset with physics-based properties.
    
    Args:
        output_path: Path to save the CSV file.
        min_entries: Minimum number of entries to generate.
        defect_density_range: (min, max) for defect density.
        seed: Random seed for reproducibility.
        version: Version string (e.g., git hash).
    
    Returns:
        Path to the generated file.
    """
    np.random.seed(seed)
    
    # Ensure output directory exists
    ensure_output_directories()
    
    # Generate defect types
    defect_types = ['vacancy', 'substitution', 'grain_boundary', 'edge_dislocation']
    
    # Generate data
    data = []
    for i in range(min_entries):
        defect_type = np.random.choice(defect_types)
        density = np.random.uniform(*defect_density_range)
        
        # Base material properties (normalized)
        base_conductivity = 1.0
        base_modulus = 1.0
        base_strength = 1.0
        
        # Apply physics-based models
        conductivity = apply_matthiessen_rule(density, base_conductivity)
        modulus = apply_rule_of_mixtures(density, base_modulus)
        strength = apply_griffith_criterion(density, base_strength)
        
        # Add small random noise for realism (within physical bounds)
        conductivity += np.random.normal(0, 0.01 * conductivity)
        modulus += np.random.normal(0, 0.01 * modulus)
        strength += np.random.normal(0, 0.01 * strength)
        
        # Ensure non-negative
        conductivity = max(0.0, conductivity)
        modulus = max(0.0, modulus)
        strength = max(0.0, strength)
        
        # Elastic tensor (simplified as a scalar for this example, or a string representation)
        # In a real scenario, this would be a matrix. Here we store a simplified scalar trace.
        elastic_tensor_val = modulus * 3.0  # Approximate trace for isotropic material
        
        entry = {
            'defect_type': defect_type,
            'defect_density': density,
            'conductivity': conductivity,
            'elastic_tensor': elastic_tensor_val,
            'fracture_energy': strength * 0.5,  # Simplified relation
            'data_source': 'synthetic',
            'version': version,
            'seed': seed
        }
        data.append(entry)
    
    # Write to CSV
    fieldnames = list(data[0].keys())
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Generated {len(data)} synthetic entries to {output_path}")
    return output_path

def generate_synthetic_holdout_data(
    output_path: str,
    min_entries: int = 50,
    seed: int = 43, # Distinct seed for holdout
    version: str = "unknown"
) -> str:
    """
    Generate hold-out synthetic data using a distinct physics engine (GP Surrogate).
    For this implementation, we use slightly perturbed parameters to simulate a distinct engine.
    """
    np.random.seed(seed)
    ensure_output_directories()
    
    defect_types = ['vacancy', 'substitution', 'grain_boundary', 'edge_dislocation']
    data = []
    
    for i in range(min_entries):
        defect_type = np.random.choice(defect_types)
        density = np.random.uniform(0.001, 0.1)
        
        # Perturbed parameters for "distinct engine"
        k_griffith = 1.5 + np.random.normal(0, 0.1)
        alpha_rome = 2.0 + np.random.normal(0, 0.1)
        beta_matthiessen = 3.0 + np.random.normal(0, 0.1)
        
        base_conductivity = 1.0
        base_modulus = 1.0
        base_strength = 1.0
        
        conductivity = base_conductivity / (1 + beta_matthiessen * density)
        modulus = base_modulus * (1 - alpha_rome * density)
        strength = base_strength * (1 - k_griffith * density)
        
        # Bounds
        conductivity = max(0.0, conductivity)
        modulus = max(0.0, modulus)
        strength = max(0.0, strength)
        
        elastic_tensor_val = modulus * 3.0
        
        entry = {
            'defect_type': defect_type,
            'defect_density': density,
            'conductivity': conductivity,
            'elastic_tensor': elastic_tensor_val,
            'fracture_energy': strength * 0.5,
            'data_source': 'synthetic_holdout',
            'version': version,
            'seed': seed
        }
        data.append(entry)
    
    fieldnames = list(data[0].keys())
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Generated {len(data)} holdout synthetic entries to {output_path}")
    return output_path

def save_to_csv(data: List[Dict], output_path: str) -> None:
    """Helper to save data to CSV."""
    if not data:
        return
    fieldnames = list(data[0].keys())
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def main():
    """Main entry point for generating synthetic data."""
    ensure_output_directories()
    git_hash = get_git_hash()
    
    # Generate primary training set
    train_path = get_project_root() / 'data' / 'raw' / 'synthetic_train.csv'
    generate_synthetic_data(str(train_path), min_entries=100, seed=42, version=git_hash)
    
    # Generate hold-out set
    holdout_path = get_project_root() / 'data' / 'raw' / 'synthetic_holdout.csv'
    generate_synthetic_holdout_data(str(holdout_path), min_entries=50, seed=43, version=git_hash)
    
    logger.info("Synthetic data generation complete.")

if __name__ == "__main__":
    main()
