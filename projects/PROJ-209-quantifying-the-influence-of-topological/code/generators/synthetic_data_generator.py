"""
Synthetic Data Generator for 2D Material Defect Properties.

Implements the surrogate model described in T013:
- Analytical Signal: Continuum elasticity (E = E0 * (1 - k*density))
- Noise: Gaussian (sigma=0.05) calibrated from DFT dataset
- Generates train and holdout sets with seed=42 for reproducibility.
"""
import os
import csv
import json
import hashlib
import subprocess
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Project root resolution (relative to code/generators)
def get_project_root() -> Path:
    """Returns the absolute path to the project root."""
    current = Path(__file__).resolve()
    # Navigate up from code/generators to root
    return current.parent.parent

def ensure_output_directories() -> None:
    """Creates necessary output directories if they don't exist."""
    root = get_project_root()
    dirs = [
        root / "data" / "raw",
        root / "data" / "state",
        root / "data" / "processed"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_git_hash() -> str:
    """Returns the current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=get_project_root(),
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"

def compute_sha256(filepath: Path) -> str:
    """Computes SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def apply_griffith_criterion(fracture_energy: float, elastic_modulus: float, flaw_size: float) -> float:
    """
    Calculates fracture strength using Griffith criterion.
    sigma_f = sqrt(2 * E * gamma / (pi * a))
    """
    if flaw_size <= 0:
        return 0.0
    return np.sqrt((2 * elastic_modulus * fracture_energy) / (np.pi * flaw_size))

def apply_rule_of_mixtures(base_val: float, defect_fraction: float, modifier: float) -> float:
    """
    Simple rule of mixtures for property degradation.
    P = P0 * (1 - k * defect_fraction)
    """
    return base_val * (1 - modifier * defect_fraction)

def apply_matthiessen_rule(base_conductivity: float, scattering_rate: float) -> float:
    """
    Approximates conductivity reduction due to defects.
    1/sigma_total = 1/sigma0 + 1/sigma_defect
    Simplified: sigma = sigma0 / (1 + k * scattering)
    """
    return base_conductivity / (1 + 0.5 * scattering_rate)

def generate_synthetic_data(
    n_samples: int,
    seed: int,
    pristine_references: Dict[str, float],
    defect_materials: List[str] = ["graphene", "MoS2"]
) -> List[Dict[str, Any]]:
    """
    Generates synthetic dataset based on continuum elasticity models.
    
    Args:
        n_samples: Number of samples to generate.
        seed: Random seed for reproducibility.
        pristine_references: Dictionary of pristine property values (E0, sigma0, etc.).
        defect_materials: List of materials to simulate.
        
    Returns:
        List of dictionaries representing the synthetic dataset rows.
    """
    np.random.seed(seed)
    data = []
    
    # Default pristine values if not provided
    E0 = pristine_references.get("E0", 1000.0)  # GPa
    sigma0 = pristine_references.get("sigma0", 130.0)  # GPa
    gamma0 = pristine_references.get("gamma0", 10.0)  # J/m^2
    kappa0 = pristine_references.get("kappa0", 1000.0)  # S/m (thermal/electrical)

    # Parameters for the analytical model
    k_elastic = 0.8  # Elastic degradation factor
    k_conductivity = 1.2  # Conductivity degradation factor
    k_fracture = 0.5  # Fracture energy degradation factor
    noise_sigma = 0.05  # Gaussian noise standard deviation (5%)

    for i in range(n_samples):
        material = np.random.choice(defect_materials)
        
        # Generate defect density in realistic range [0, 0.1]
        density = np.random.uniform(0.001, 0.1)
        
        # Defect type (categorical)
        defect_types = ["vacancy", "substitution", "grain_boundary", "dislocation"]
        defect_type = np.random.choice(defect_types)
        
        # Base properties for this material
        mat_E0 = E0 if material == "graphene" else 300.0
        mat_sigma0 = sigma0 if material == "graphene" else 20.0
        mat_gamma0 = gamma0 if material == "graphene" else 5.0
        mat_kappa0 = kappa0 if material == "graphene" else 5000.0

        # Analytical Signal: Continuum Elasticity
        # E = E0 * (1 - k * density)
        base_elastic = mat_E0 * (1 - k_elastic * density)
        base_conductivity = mat_kappa0 * (1 - k_conductivity * density)
        base_fracture_energy = mat_gamma0 * (1 - k_fracture * density)
        
        # Add Gaussian Noise (calibrated from DFT)
        # Ensure values stay positive
        noise_E = np.random.normal(0, noise_sigma * base_elastic)
        noise_sigma_prop = np.random.normal(0, noise_sigma * base_conductivity)
        noise_gamma = np.random.normal(0, noise_sigma * base_fracture_energy)
        
        elastic_modulus = max(0.1, base_elastic + noise_E)
        conductivity = max(0.1, base_conductivity + noise_sigma_prop)
        fracture_energy = max(0.1, base_fracture_energy + noise_gamma)
        
        # Calculate Fracture Strength using Griffith Criterion
        # Assume a characteristic flaw size related to defect density
        flaw_size = 1e-9 * (1 + 100 * density) # nm -> m scale approximation
        fracture_strength = apply_griffith_criterion(fracture_energy, elastic_modulus, flaw_size)
        
        row = {
            "id": f"synth_{i:04d}",
            "material": material,
            "defect_type": defect_type,
            "defect_density": density,
            "elastic_modulus_GPa": elastic_modulus,
            "conductivity_S_m": conductivity,
            "fracture_energy_J_m2": fracture_energy,
            "fracture_strength_GPa": fracture_strength,
            "synthetic": True
        }
        data.append(row)
        
    return data

def save_to_csv(data: List[Dict[str, Any]], filepath: Path) -> None:
    """Saves a list of dictionaries to a CSV file."""
    if not data:
        return
    fieldnames = data[0].keys()
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def generate_holdout_data(
    n_samples: int,
    seed: int,
    pristine_references: Dict[str, float],
    defect_materials: List[str] = ["graphene", "MoS2"]
) -> List[Dict[str, Any]]:
    """
    Generates a distinct holdout set using a different seed or parameters.
    """
    # Use a different seed offset to ensure distinctness but reproducibility
    holdout_seed = seed + 1000
    return generate_synthetic_data(n_samples, holdout_seed, pristine_references, defect_materials)

def load_pristine_references() -> Dict[str, float]:
    """
    Loads pristine reference values.
    Tries to load from data/raw/pristine_structures.csv if it exists,
    otherwise uses defaults.
    """
    root = get_project_root()
    path = root / "data" / "raw" / "pristine_structures.csv"
    
    if path.exists():
        # Try to parse the CSV to get averages
        # Expected columns: material, elastic_modulus, conductivity, fracture_energy
        try:
            with open(path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            if not rows:
                return {"E0": 1000.0, "sigma0": 130.0, "gamma0": 10.0, "kappa0": 1000.0}
            
            # Simple averaging for now
            e_vals = [float(r['elastic_modulus']) for r in rows if r.get('elastic_modulus')]
            s_vals = [float(r['conductivity']) for r in rows if r.get('conductivity')]
            g_vals = [float(r['fracture_energy']) for r in rows if r.get('fracture_energy')]
            
            return {
                "E0": np.mean(e_vals) if e_vals else 1000.0,
                "sigma0": np.mean(s_vals) if s_vals else 130.0,
                "gamma0": np.mean(g_vals) if g_vals else 10.0,
                "kappa0": np.mean(s_vals) * 10 if s_vals else 1000.0 # Rough proxy
            }
        except (ValueError, KeyError):
            pass
    
    # Fallback defaults
    return {"E0": 1000.0, "sigma0": 130.0, "gamma0": 10.0, "kappa0": 1000.0}

def main():
    """
    Main entry point for synthetic data generation.
    Reads generation_status.json to determine if synthetic data is needed.
    """
    root = get_project_root()
    ensure_output_directories()
    
    status_path = root / "data" / "state" / "generation_status.json"
    
    # Check if synthetic generation is triggered
    if not status_path.exists():
        print("Error: data/state/generation_status.json not found. Cannot proceed.")
        return
    
    with open(status_path, 'r') as f:
        status = json.load(f)
    
    if status.get("source") != "synthetic":
        print("Status indicates source is not synthetic. Skipping generation.")
        return
    
    print("Starting Synthetic Data Generation (T013)...")
    
    # Load pristine references
    refs = load_pristine_references()
    
    # Generate Train Set (N=1000)
    train_seed = 42
    train_data = generate_synthetic_data(1000, train_seed, refs)
    train_path = root / "data" / "raw" / "synthetic_train.csv"
    save_to_csv(train_data, train_path)
    print(f"Generated {len(train_data)} training samples at {train_path}")
    
    # Generate Holdout Set (N=200)
    holdout_data = generate_holdout_data(200, train_seed, refs)
    holdout_path = root / "data" / "raw" / "synthetic_holdout.csv"
    save_to_csv(holdout_data, holdout_path)
    print(f"Generated {len(holdout_data)} holdout samples at {holdout_path}")
    
    # Write Configuration
    config = {
        "seed": train_seed,
        "analytical_formula": "E = E0 * (1 - k*density)",
        "parameters": {
            "k_elastic": 0.8,
            "k_conductivity": 1.2,
            "k_fracture": 0.5,
            "noise_sigma": 0.05
        },
        "pristine_references": refs,
        "git_hash": get_git_hash(),
        "train_count": len(train_data),
        "holdout_count": len(holdout_data)
    }
    
    config_path = root / "data" / "state" / "synthetic_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"Configuration saved to {config_path}")
    
    print("Synthetic Data Generation Complete.")

if __name__ == "__main__":
    main()