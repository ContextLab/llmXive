import os
import csv
import json
import hashlib
import subprocess
import numpy as np
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from infrastructure
from infrastructure.path_utils import get_project_root, ensure_dir

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_git_hash() -> str:
    """Get the current git commit hash for versioning."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()[:8]
    except subprocess.CalledProcessError:
        logger.warning("Git not available or not a git repo. Using 'no-git'.")
        return "no-git"

def ensure_output_directories() -> None:
    """Ensure all required output directories exist."""
    project_root = get_project_root()
    dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
    ]
    for d in dirs:
        ensure_dir(d)

def apply_griffith_criterion(energy_release_rate: float, elastic_modulus: float, crack_length: float) -> float:
    """
    Apply Griffith criterion for fracture strength.
    sigma_c = sqrt(2 * E * gamma / (pi * a))
    """
    if crack_length <= 0:
        return 0.0
    return np.sqrt(2 * elastic_modulus * energy_release_rate / (np.pi * crack_length))

def apply_rule_of_mixtures(base_val: float, defect_val: float, volume_fraction: float) -> float:
    """
    Apply Rule of Mixtures for property estimation.
    P_composite = V_m * P_m + V_f * P_f
    """
    return (1 - volume_fraction) * base_val + volume_fraction * defect_val

def apply_matthiessen_rule(base_resistivity: float, defect_resistivity: float) -> float:
    """
    Apply Matthiessen's rule for conductivity/resistivity.
    rho_total = rho_base + rho_defect
    """
    return base_resistivity + defect_resistivity

def generate_synthetic_data(
    n_samples: int = 100,
    defect_density_min: float = 0.001,
    defect_density_max: float = 0.1,
    seed: int = 42,
    version: str = "unknown"
) -> List[Dict[str, Any]]:
    """
    Generate synthetic defect data based on physics-based analytical models.
    
    Args:
        n_samples: Number of samples to generate.
        defect_density_min: Minimum defect density.
        defect_density_max: Maximum defect density.
        seed: Random seed for reproducibility.
        version: Version string (e.g., git hash).
    
    Returns:
        List of dictionaries containing generated data entries.
    """
    np.random.seed(seed)
    
    # Define material constants (approximate for graphene and MoS2)
    # Graphene: E ~ 1 TPa, gamma ~ 10 J/m^2
    # MoS2: E ~ 270 GPa, gamma ~ 5 J/m^2
    
    materials = [
        {"name": "graphene", "E_0": 1000.0, "gamma_0": 10.0, "sigma_0": 130.0, "k_0": 5000.0},
        {"name": "mos2", "E_0": 270.0, "gamma_0": 5.0, "sigma_0": 23.0, "k_0": 35.0}
    ]
    
    defect_types = ["vacancy", "substitution", "interstitial", "grain_boundary"]
    
    data = []
    
    for _ in range(n_samples):
        # Select material and defect type
        mat = np.random.choice(materials)
        defect_type = np.random.choice(defect_types)
        
        # Generate defect density
        density = np.random.uniform(defect_density_min, defect_density_max)
        
        # Calculate properties using physical models
        # 1. Elastic Modulus (Rule of Mixtures approximation)
        # Defect reduces stiffness
        E_defect = mat["E_0"] * 0.5 # Assume 50% reduction in defect core
        E_eff = apply_rule_of_mixtures(mat["E_0"], E_defect, density)
        
        # 2. Fracture Strength (Griffith criterion with effective crack size related to density)
        # Assume effective crack length a ~ 1/sqrt(density)
        a_eff = 1.0 / np.sqrt(density)
        gamma_eff = mat["gamma_0"] * (1 - 0.1 * density) # Slight reduction in surface energy
        sigma_eff = apply_griffith_criterion(gamma_eff, E_eff, a_eff)
        
        # 3. Conductivity (Matthiessen's rule approximation)
        # Defects increase resistivity, reducing conductivity
        k_base = mat["k_0"]
        # Assume defect resistivity is high
        rho_defect = 1.0 / (k_base * 0.1) # High resistivity
        rho_total = (1.0/k_base) + rho_defect * density
        k_eff = 1.0 / rho_total if rho_total > 0 else 0.0
        
        # 4. Elastic Tensor (simplified as scalar for this synthetic set, or a list of 6 components)
        # We'll generate a simplified 6-component tensor (Voigt notation)
        # Diagonal terms dominate, off-diagonal small
        tensor = [E_eff, E_eff * 0.3, E_eff * 0.3, 0.1, 0.1, 0.1]
        
        entry = {
            "defect_type": defect_type,
            "material": mat["name"],
            "density": density,
            "conductivity": k_eff,
            "elastic_tensor": json.dumps(tensor),
            "fracture_energy": gamma_eff,
            "elastic_modulus": E_eff,
            "fracture_strength": sigma_eff,
            "data_source": "synthetic",
            "version": version,
            "seed": seed
        }
        data.append(entry)
    
    return data

def generate_gp_surrogate_training_data(n_samples: int = 50, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generate training data for the Gaussian Process Surrogate.
    This would typically use distinct public DFT data or distinct analytical params.
    For this task, we generate a distinct set using different parameters.
    """
    np.random.seed(seed + 100) # Distinct seed
    
    materials = [
        {"name": "graphene", "E_0": 1000.0, "gamma_0": 10.0, "sigma_0": 130.0, "k_0": 5000.0},
        {"name": "mos2", "E_0": 270.0, "gamma_0": 5.0, "sigma_0": 23.0, "k_0": 35.0}
    ]
    
    defect_types = ["vacancy", "substitution", "interstitial", "grain_boundary"]
    data = []
    
    for _ in range(n_samples):
        mat = np.random.choice(materials)
        defect_type = np.random.choice(defect_types)
        density = np.random.uniform(0.001, 0.1)
        
        # Distinct physics engine parameters (e.g., different reduction factors)
        E_defect = mat["E_0"] * 0.6
        E_eff = apply_rule_of_mixtures(mat["E_0"], E_defect, density)
        
        a_eff = 1.0 / np.sqrt(density)
        gamma_eff = mat["gamma_0"] * (1 - 0.15 * density) # Different factor
        sigma_eff = apply_griffith_criterion(gamma_eff, E_eff, a_eff)
        
        rho_defect = 1.0 / (mat["k_0"] * 0.05) # Different factor
        rho_total = (1.0/mat["k_0"]) + rho_defect * density
        k_eff = 1.0 / rho_total if rho_total > 0 else 0.0
        
        tensor = [E_eff, E_eff * 0.35, E_eff * 0.35, 0.12, 0.12, 0.12]
        
        entry = {
            "defect_type": defect_type,
            "material": mat["name"],
            "density": density,
            "conductivity": k_eff,
            "elastic_tensor": json.dumps(tensor),
            "fracture_energy": gamma_eff,
            "elastic_modulus": E_eff,
            "fracture_strength": sigma_eff,
            "data_source": "synthetic_gp_train",
            "version": get_git_hash()
        }
        data.append(entry)
    
    return data

class GaussianProcessSurrogate:
    """
    A placeholder for the Gaussian Process Surrogate model.
    In a full implementation, this would train on gp_training_data and predict.
    """
    def __init__(self):
        self.is_fitted = False
    
    def fit(self, X, y):
        # Placeholder for GP fitting
        self.is_fitted = True
        return self
    
    def predict(self, X):
        if not self.is_fitted:
            raise RuntimeError("Model not fitted")
        # Placeholder prediction (random noise around mean)
        return np.random.normal(0, 1, size=len(X))

def generate_holdout_data(n_samples: int = 50, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generate hold-out set using the GP Surrogate logic (distinct physics).
    """
    # Generate training data for the surrogate
    train_data = generate_gp_surrogate_training_data(n_samples=200, seed=seed)
    
    # In a real scenario, we would fit the GP here and generate new points.
    # For this task, we return a distinct set of synthetic data to simulate the "Distinct Physics Engine".
    # We use a different seed and slightly different logic to ensure it's distinct.
    np.random.seed(seed + 200)
    
    materials = [
        {"name": "graphene", "E_0": 1000.0, "gamma_0": 10.0, "sigma_0": 130.0, "k_0": 5000.0},
        {"name": "mos2", "E_0": 270.0, "gamma_0": 5.0, "sigma_0": 23.0, "k_0": 35.0}
    ]
    
    defect_types = ["vacancy", "substitution", "interstitial", "grain_boundary"]
    data = []
    
    for _ in range(n_samples):
        mat = np.random.choice(materials)
        defect_type = np.random.choice(defect_types)
        density = np.random.uniform(0.001, 0.1)
        
        # Distinct parameters again
        E_defect = mat["E_0"] * 0.55
        E_eff = apply_rule_of_mixtures(mat["E_0"], E_defect, density)
        
        a_eff = 1.0 / np.sqrt(density)
        gamma_eff = mat["gamma_0"] * (1 - 0.12 * density)
        sigma_eff = apply_griffith_criterion(gamma_eff, E_eff, a_eff)
        
        rho_defect = 1.0 / (mat["k_0"] * 0.08)
        rho_total = (1.0/mat["k_0"]) + rho_defect * density
        k_eff = 1.0 / rho_total if rho_total > 0 else 0.0
        
        tensor = [E_eff, E_eff * 0.32, E_eff * 0.32, 0.11, 0.11, 0.11]
        
        entry = {
            "defect_type": defect_type,
            "material": mat["name"],
            "density": density,
            "conductivity": k_eff,
            "elastic_tensor": json.dumps(tensor),
            "fracture_energy": gamma_eff,
            "elastic_modulus": E_eff,
            "fracture_strength": sigma_eff,
            "data_source": "synthetic_holdout",
            "version": get_git_hash()
        }
        data.append(entry)
    
    return data

def save_to_csv(data: List[Dict[str, Any]], filename: str) -> None:
    """Save data to a CSV file."""
    if not data:
        logger.warning("No data to save.")
        return
    
    output_path = get_project_root() / "data" / "raw" / filename
    ensure_dir(output_path.parent)
    
    fieldnames = data[0].keys()
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Saved {len(data)} entries to {output_path}")

def main():
    """Entry point for the generator script."""
    ensure_output_directories()
    
    # Generate primary training data
    train_data = generate_synthetic_data(n_samples=150, seed=42)
    save_to_csv(train_data, "synthetic_train.csv")
    
    # Generate holdout data
    holdout_data = generate_holdout_data(n_samples=50, seed=42)
    save_to_csv(holdout_data, "synthetic_holdout.csv")
    
    logger.info("Synthetic data generation complete.")

if __name__ == "__main__":
    main()