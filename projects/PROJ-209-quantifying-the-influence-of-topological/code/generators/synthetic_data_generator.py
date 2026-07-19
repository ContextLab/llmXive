import os
import csv
import json
import hashlib
import subprocess
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Constants
SEED_TRAIN = 42
SEED_HOLDOUT = 12345  # Distinct seed for hold-out generation
N_HOLDOUT = 200

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def ensure_output_directories() -> None:
    """Ensure all required output directories exist."""
    project_root = get_project_root()
    dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "state",
        project_root / "data" / "validation"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_git_hash() -> str:
    """Get the current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "no-git"

def apply_griffith_criterion(density: float, base_strength: float, modulus: float) -> float:
    """
    Apply Griffith criterion for fracture strength reduction due to defects.
    sigma_f = sigma_0 * sqrt(1 - c * rho)
    """
    c = 0.5  # Empirical constant
    factor = max(0.0, 1.0 - c * density)
    return base_strength * np.sqrt(factor)

def apply_rule_of_mixtures(density: float, base_modulus: float) -> float:
    """
    Apply rule of mixtures for elastic modulus reduction.
    E = E_0 * (1 - alpha * rho)
    """
    alpha = 0.3  # Empirical constant
    return base_modulus * (1.0 - alpha * density)

def apply_matthiessen_rule(density: float, base_conductivity: float) -> float:
    """
    Apply Matthiessen's rule for conductivity reduction.
    1/sigma = 1/sigma_0 + beta * rho
    """
    beta = 0.1  # Empirical constant
    inv_sigma = (1.0 / base_conductivity) + (beta * density)
    return 1.0 / inv_sigma

def generate_holdout_data(n_samples: int = N_HOLDOUT, seed: int = SEED_HOLDOUT) -> List[Dict[str, Any]]:
    """
    Generate synthetic hold-out data with distinct physics engine configuration (distinct seed).
    
    This function generates data using the same physical models as the training set
    but with a different random seed to ensure independence for validation.
    
    Args:
        n_samples: Number of samples to generate
        seed: Random seed for reproducibility (distinct from training seed=42)
    
    Returns:
        List of dictionaries containing generated data points
    """
    np.random.seed(seed)
    
    ensure_output_directories()
    
    # Define base material properties for pristine graphene and MoS2
    materials = {
        "graphene": {
            "conductivity": 1.0e6,  # S/m
            "youngs_modulus": 1000.0,  # GPa
            "fracture_strength": 130.0,  # GPa
            "density_range": (0.0, 0.1)  # Defect density range
        },
        "MoS2": {
            "conductivity": 1.0e2,  # S/m
            "youngs_modulus": 330.0,  # GPa
            "fracture_strength": 23.0,  # GPa
            "density_range": (0.0, 0.15)
        }
    }
    
    defect_types = ["vacancy", "substitution", "grain_boundary", "edge_defect"]
    
    data = []
    
    for _ in range(n_samples):
        # Randomly select material
        material = np.random.choice(list(materials.keys()))
        props = materials[material]
        
        # Randomly select defect type
        defect_type = np.random.choice(defect_types)
        
        # Generate defect density within material-specific range
        density = np.random.uniform(*props["density_range"])
        
        # Calculate properties using physics-informed models
        conductivity = apply_matthiessen_rule(density, props["conductivity"])
        youngs_modulus = apply_rule_of_mixtures(density, props["youngs_modulus"])
        fracture_strength = apply_griffith_criterion(
            density, 
            props["fracture_strength"], 
            props["youngs_modulus"]
        )
        
        # Add small Gaussian noise to simulate measurement uncertainty
        # Noise level: 1% of value
        conductivity *= (1.0 + 0.01 * np.random.randn())
        youngs_modulus *= (1.0 + 0.01 * np.random.randn())
        fracture_strength *= (1.0 + 0.01 * np.random.randn())
        
        # Ensure non-negative values
        conductivity = max(0.0, conductivity)
        youngs_modulus = max(0.0, youngs_modulus)
        fracture_strength = max(0.0, fracture_strength)
        
        entry = {
            "defect_id": f"holdout_{material}_{defect_type}_{_}",
            "material": material,
            "defect_type": defect_type,
            "defect_density": round(density, 6),
            "conductivity": round(conductivity, 6),
            "youngs_modulus": round(youngs_modulus, 4),
            "fracture_strength": round(fracture_strength, 4),
            "generation_seed": seed,
            "is_holdout": True
        }
        data.append(entry)
    
    return data

def save_to_csv(data: List[Dict[str, Any]], filepath: str) -> None:
    """Save data list to CSV file."""
    if not data:
        raise ValueError("Cannot save empty data list")
    
    fieldnames = list(data[0].keys())
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def main():
    """Main entry point for hold-out data generation."""
    print("Starting synthetic hold-out data generation...")
    
    # Generate hold-out data with distinct seed
    holdout_data = generate_holdout_data(n_samples=N_HOLDOUT, seed=SEED_HOLDOUT)
    
    # Save to CSV
    project_root = get_project_root()
    output_path = project_root / "data" / "raw" / "synthetic_holdout.csv"
    
    save_to_csv(holdout_data, str(output_path))
    
    # Log generation metadata
    metadata = {
        "seed": SEED_HOLDOUT,
        "n_samples": N_HOLDOUT,
        "git_hash": get_git_hash(),
        "output_file": str(output_path),
        "distinct_from_training": True,
        "physics_model": "griffith_rule_mixture_matthiessen"
    }
    
    metadata_path = project_root / "data" / "state" / "holdout_generation_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Successfully generated {N_HOLDOUT} hold-out samples.")
    print(f"Output saved to: {output_path}")
    print(f"Metadata saved to: {metadata_path}")

if __name__ == "__main__":
    main()
