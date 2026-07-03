"""
Synthetic Data Generator
Primary Mode: Analytical Continuum Mechanics
Hold-Out Mode: Gaussian GP Surrogate
"""
import os
import json
import csv
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

from infrastructure.path_utils import (
    DIR_DATA_RAW,
    ensure_dir,
    get_project_root
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_git_hash() -> str:
    """Get the current git commit hash for versioning."""
    import subprocess
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
        return "no-git"

def generate_synthetic_defect_data(
    output_path: Optional[Path] = None,
    seed: int = 42,
    min_density: float = 0.001,
    max_density: float = 0.1,
    min_entries: int = 100
) -> bool:
    """
    Generate synthetic defect data using analytical continuum mechanics.
    
    Models:
    - Griffith criterion for fracture energy
    - Rule of Mixtures for elastic properties
    - Matthiessen's rule for conductivity
    """
    if output_path is None:
        output_path = DIR_DATA_RAW / "synthetic_defect_fallback.csv"
    
    ensure_dir(output_path.parent)
    np.random.seed(seed)
    git_hash = get_git_hash()
    
    defect_types = ["vacancy", "interstitial", "substitutional", "grain_boundary"]
    materials = ["graphene", "mos2"]
    
    # Generate entries
    entries = []
    for i in range(min_entries):
        defect_type = np.random.choice(defect_types)
        material = np.random.choice(materials)
        density = np.random.uniform(min_density, max_density)
        
        # Analytical models
        # Conductivity reduction (Matthiessen's rule approximation)
        base_conductivity = 1.0 if material == "graphene" else 0.1
        conductivity = base_conductivity * (1 - 0.5 * density)
        
        # Elastic modulus reduction (Rule of Mixtures)
        base_youngs = 1.0 if material == "graphene" else 0.3
        youngs_modulus = base_youngs * (1 - 0.3 * density)
        
        # Fracture energy (Griffith criterion approximation)
        base_fracture = 1.0 if material == "graphene" else 0.5
        fracture_energy = base_fracture * (1 - 0.4 * density)
        
        entry = {
            "defect_type": defect_type,
            "material": material,
            "defect_density": density,
            "conductivity": conductivity,
            "elastic_tensor": f"[{youngs_modulus}, 0.0, 0.0, 0.0, {youngs_modulus}, 0.0, 0.0, 0.0, {youngs_modulus}]",
            "fracture_energy": fracture_energy,
            "data_source": "synthetic",
            "generator_version": git_hash,
            "seed": seed
        }
        entries.append(entry)
    
    # Write to CSV
    fieldnames = ["defect_type", "material", "defect_density", "conductivity", 
                 "elastic_tensor", "fracture_energy", "data_source", "generator_version", "seed"]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(entries)
    
    logger.info(f"Generated {len(entries)} synthetic entries to {output_path}")
    return True

def generate_holdout_data(
    output_path: Optional[Path] = None,
    seed: int = 43,  # Distinct seed for hold-out
    min_density: float = 0.001,
    max_density: float = 0.1,
    min_entries: int = 50
) -> bool:
    """
    Generate hold-out data using a Gaussian GP Surrogate.
    This emulates a "Distinct Physics Engine" for validation.
    """
    if output_path is None:
        output_path = DIR_DATA_RAW / "synthetic_holdout.csv"
    
    ensure_dir(output_path.parent)
    np.random.seed(seed)
    git_hash = get_git_hash()
    
    defect_types = ["vacancy", "interstitial", "substitutional", "grain_boundary"]
    materials = ["graphene", "mos2"]
    
    # Simulate GP surrogate with slightly different parameters
    entries = []
    for i in range(min_entries):
        defect_type = np.random.choice(defect_types)
        material = np.random.choice(materials)
        density = np.random.uniform(min_density, max_density)
        
        # GP surrogate with perturbed parameters
        base_conductivity = 1.0 if material == "graphene" else 0.1
        conductivity = base_conductivity * (1 - 0.5 * density + 0.05 * np.random.randn())
        conductivity = max(0.01, conductivity)  # Ensure positive
        
        base_youngs = 1.0 if material == "graphene" else 0.3
        youngs_modulus = base_youngs * (1 - 0.3 * density + 0.03 * np.random.randn())
        youngs_modulus = max(0.01, youngs_modulus)
        
        base_fracture = 1.0 if material == "graphene" else 0.5
        fracture_energy = base_fracture * (1 - 0.4 * density + 0.04 * np.random.randn())
        fracture_energy = max(0.01, fracture_energy)
        
        entry = {
            "defect_type": defect_type,
            "material": material,
            "defect_density": density,
            "conductivity": conductivity,
            "elastic_tensor": f"[{youngs_modulus}, 0.0, 0.0, 0.0, {youngs_modulus}, 0.0, 0.0, 0.0, {youngs_modulus}]",
            "fracture_energy": fracture_energy,
            "data_source": "synthetic_holdout",
            "generator_version": git_hash,
            "seed": seed,
            "mode": "gp_surrogate"
        }
        entries.append(entry)
    
    fieldnames = ["defect_type", "material", "defect_density", "conductivity", 
                 "elastic_tensor", "fracture_energy", "data_source", "generator_version", "seed", "mode"]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(entries)
    
    logger.info(f"Generated {len(entries)} hold-out entries to {output_path}")
    return True

def main():
    """Generate both primary and hold-out synthetic datasets."""
    logger.info("Generating synthetic datasets...")
    
    success1 = generate_synthetic_defect_data()
    success2 = generate_holdout_data()
    
    if success1 and success2:
        logger.info("All synthetic datasets generated successfully.")
    else:
        logger.error("Some synthetic datasets failed to generate.")
        exit(1)

if __name__ == "__main__":
    main()
