import os
import csv
import json
import hashlib
import subprocess
import numpy as np
import logging
from typing import List, Dict, Optional
from pathlib import Path

from infrastructure.path_utils import get_project_root, ensure_dir

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_git_hash() -> str:
    """Get the current git commit hash for versioning."""
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
    except Exception:
        return "no-git"

def ensure_output_directories() -> None:
    """Ensure all required output directories exist."""
    root = get_project_root()
    dirs = [root / "data" / "raw"]
    for d in dirs:
        ensure_dir(d)

def apply_griffith_criterion(energy_release_rate: float, elastic_modulus: float, crack_length: float) -> float:
    """
    Apply Griffith criterion for fracture strength.
    sigma_f = sqrt(2 * E * gamma / (pi * a))
    """
    if crack_length <= 0 or elastic_modulus <= 0:
        return 0.0
    return np.sqrt((2 * elastic_modulus * energy_release_rate) / (np.pi * crack_length))

def apply_rule_of_mixtures(matrix_prop: float, inclusion_prop: float, volume_fraction: float) -> float:
    """
    Apply Rule of Mixtures for effective property.
    P_eff = P_m * (1 - V_f) + P_i * V_f
    """
    return matrix_prop * (1 - volume_fraction) + inclusion_prop * volume_fraction

def apply_matthiessen_rule(base_resistivity: float, defect_resistivity: float, defect_density: float) -> float:
    """
    Apply Matthiessen's rule for conductivity/resistivity.
    rho_total = rho_base + rho_defect * density
    Conductivity = 1 / rho_total
    """
    rho_total = base_resistivity + defect_resistivity * defect_density
    if rho_total <= 0:
        return 0.0
    return 1.0 / rho_total

def generate_synthetic_defect_data(output_path: str, count: int = 100, seed: int = 42, version: str = "unknown") -> None:
    """
    Generate synthetic defect data based on physics-based models.
    - Defect density in [0.001, 0.1]
    - Generates >= count entries.
    - Sets data_source = 'synthetic'.
    - Includes git hash versioning.
    """
    np.random.seed(seed)
    ensure_output_directories()
    
    # Physical constants / reference values (approximate for graphene/MoS2)
    # Graphene
    E_graphene = 1000.0  # GPa
    sigma_0_graphene = 130.0  # GPa
    cond_0_graphene = 1.0  # arbitrary units
    
    # MoS2
    E_mos2 = 270.0
    sigma_0_mos2 = 23.0
    cond_0_mos2 = 0.001
    
    materials = ["graphene", "MoS2"]
    defect_types = ["vacancy", "substitution", "grain_boundary", "adatom"]
    
    rows = []
    
    for i in range(count):
        mat = np.random.choice(materials)
        defect_type = np.random.choice(defect_types)
        
        # Defect density in [0.001, 0.1]
        density = np.random.uniform(0.001, 0.1)
        
        # Reference properties
        if mat == "graphene":
            E_ref = E_graphene
            sigma_ref = sigma_0_graphene
            cond_ref = cond_0_graphene
        else:
            E_ref = E_mos2
            sigma_ref = sigma_0_mos2
            cond_ref = cond_0_mos2
        
        # Generate properties using physics models
        # 1. Elastic Modulus (Rule of Mixtures) - Defects usually reduce stiffness
        # Assume inclusion (defect) has much lower modulus
        E_defect = E_ref * 0.1
        E_eff = apply_rule_of_mixtures(E_ref, E_defect, density)
        
        # 2. Fracture Strength (Griffith Criterion)
        # sigma_f = sigma_0 * (1 - k * density) approx, or using crack length proportional to density
        # Simulating crack length a ~ density
        a = density * 10.0  # arbitrary scaling
        gamma = 1.0  # surface energy
        # sigma_f = sqrt(2 * E * gamma / (pi * a))
        # Normalize to reference to avoid extreme values
        sigma_f_raw = apply_griffith_criterion(gamma, E_eff, a)
        # Scale to be reasonable relative to reference
        sigma_f = sigma_ref * (sigma_f_raw / (sigma_ref + 1e-6)) 
        # Ensure it's not higher than pristine and not negative
        sigma_f = min(sigma_f, sigma_ref)
        sigma_f = max(sigma_f, sigma_ref * 0.1)
        
        # 3. Conductivity (Matthiessen's Rule)
        # rho_total = rho_base + rho_defect * density
        # Assume defect adds significant resistivity
        rho_base = 1.0 / cond_ref
        rho_defect_factor = 100.0
        rho_total = rho_base + rho_defect_factor * density
        cond_eff = 1.0 / rho_total
        
        # Add some noise
        noise_factor = 1.0 + np.random.normal(0, 0.05)
        E_eff *= noise_factor
        sigma_f *= noise_factor
        cond_eff *= noise_factor
        
        # Elastic tensor (simplified as string representation of a 6x6 matrix diagonal for isotropic approx)
        # Just a placeholder string for the required column
        elastic_tensor_str = f"[[{E_eff}, 0, 0], [0, {E_eff}, 0], [0, 0, {E_eff}]]"
        
        row = {
            "defect_type": defect_type,
            "density": f"{density:.6f}",
            "conductivity": f"{cond_eff:.6e}",
            "elastic_tensor": elastic_tensor_str,
            "fracture_energy": f"{sigma_f:.6f}",
            "material": mat,
            "data_source": "synthetic",
            "version": version,
            "seed": str(seed)
        }
        rows.append(row)
    
    # Write to CSV
    ensure_dir(Path(output_path).parent)
    fieldnames = list(rows[0].keys())
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"Generated {count} synthetic entries to {output_path}")

def main():
    root = get_project_root()
    output = str(root / "data" / "raw" / "synthetic_defect_fallback.csv")
    generate_synthetic_defect_data(output, count=100, seed=42, version=get_git_hash())

if __name__ == "__main__":
    main()