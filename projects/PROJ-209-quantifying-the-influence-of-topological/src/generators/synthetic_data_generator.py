"""
Synthetic Data Generator for 2D Material Defect Properties.

This module provides two modes of synthetic data generation:
1. Primary Mode: Analytical Continuum Mechanics (Griffith criterion, Rule of Mixtures, Matthiessen's rule).
2. Hold-Out Mode: Gaussian Process (GP) Surrogate trained on distinct analytical parameters to emulate a "Distinct Physics Engine".
"""

import os
import csv
import hashlib
import random
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# External dependencies
import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C
from sklearn.model_selection import train_test_split

# Project imports
try:
    from config import get_project_root, get_seed
except ImportError:
    # Fallback for standalone execution context if config is not in path yet
    from pathlib import Path
    def get_project_root():
        return Path(__file__).parent.parent.parent
    def get_seed():
        return 42

def get_git_hash() -> str:
    """Attempt to get the current git commit hash for versioning."""
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            cwd=get_project_root(),
            capture_output=True,
            text=True
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"

def generate_primary_synthetic_data(
    n_samples: int = 100,
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Primary Mode: Generate data using Analytical Continuum Mechanics.
    Uses Griffith criterion, Rule of Mixtures, and Matthiessen's rule.
    """
    random.seed(seed)
    np.random.seed(seed)
    
    defect_types = ["vacancy", "substitution", "grain_boundary", "edge_dislocation"]
    materials = ["graphene", "mos2"]
    
    # Base properties (pristine)
    base_props = {
        "graphene": {"sigma_0": 6000.0, "E_0": 1000.0, "sigma_f_0": 130.0}, # Conductivity, Young's Modulus (GPa), Fracture Strength (GPa)
        "mos2": {"sigma_0": 100.0, "E_0": 270.0, "sigma_f_0": 25.0}
    }

    data = []
    for _ in range(n_samples):
        mat = random.choice(materials)
        dtype = random.choice(defect_types)
        density = random.uniform(0.001, 0.1)
        
        props = base_props[mat]
        
        # Analytical Models
        # 1. Conductivity (Matthiessen's rule approximation: 1/sigma = 1/sigma_0 + k*rho)
        k_cond = 5000.0 if dtype == "vacancy" else 2000.0
        sigma = 1.0 / (1.0/props["sigma_0"] + k_cond * density)
        
        # 2. Young's Modulus (Rule of Mixtures / Linear degradation)
        k_E = 0.8 if dtype == "grain_boundary" else 0.5
        E = props["E_0"] * (1.0 - k_E * density)
        
        # 3. Fracture Strength (Griffith criterion approximation: sigma_f ~ 1/sqrt(a) ~ 1/sqrt(rho))
        # Simplified: sigma_f = sigma_f_0 * (1 - c * sqrt(rho))
        c_griffith = 2.5
        sigma_f = props["sigma_f_0"] * (1.0 - c_griffith * math.sqrt(density))
        sigma_f = max(0.1, sigma_f) # Physical bound

        entry = {
            "material": mat,
            "defect_type": dtype,
            "defect_density": density,
            "conductivity": sigma,
            "elastic_tensor_diag": [E, E, 0.3*E, 0.3*E, 0.3*E, 0.3*E], # Simplified isotropic approximation
            "fracture_energy": sigma_f * sigma_f / E * 10.0, # Rough proxy
            "data_source": "analytical",
            "version": get_git_hash()
        }
        data.append(entry)
    
    return data

def generate_holdout_synthetic_data(
    n_samples: int = 50,
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Hold-Out Mode: Use a Gaussian GP Surrogate trained on distinct analytical params.
    This emulates a "Distinct Physics Engine" by learning a non-linear mapping
    from a slightly perturbed set of "training" data generated with different physics constants.
    """
    random.seed(seed)
    np.random.seed(seed)
    
    defect_types = ["vacancy", "substitution", "grain_boundary", "edge_dislocation"]
    materials = ["graphene", "mos2"]
    
    # Distinct Physics Engine Parameters (for training the GP surrogate)
    # These are intentionally different from the Primary Mode to simulate a distinct source
    distinct_base_props = {
        "graphene": {"sigma_0": 5800.0, "E_0": 980.0, "sigma_f_0": 125.0}, 
        "mos2": {"sigma_0": 95.0, "E_0": 260.0, "sigma_f_0": 24.0}
    }

    # 1. Generate a "Training" dataset for the GP using the Distinct Physics Engine
    # We generate a larger set to train the surrogate
    n_train = 300
    X_train_list = []
    y_train_list = {"sigma": [], "E": [], "sigma_f": []}
    
    # One-hot encoding for defect type (4 types)
    type_map = {t: i for i, t in enumerate(defect_types)}
    mat_map = {m: i for i, m in enumerate(materials)}
    
    for _ in range(n_train):
        mat = random.choice(materials)
        dtype = random.choice(defect_types)
        density = random.uniform(0.001, 0.1)
        
        props = distinct_base_props[mat]
        
        # Distinct analytical models (different coefficients)
        # Conductivity: Different scattering factor
        k_cond_dist = 6000.0 if dtype == "vacancy" else 2500.0
        sigma = 1.0 / (1.0/props["sigma_0"] + k_cond_dist * density)
        
        # Young's Modulus: Different degradation factor
        k_E_dist = 0.9 if dtype == "grain_boundary" else 0.6
        E = props["E_0"] * (1.0 - k_E_dist * density)
        
        # Fracture Strength: Different Griffith constant
        c_griffith_dist = 2.8
        sigma_f = props["sigma_f_0"] * (1.0 - c_griffith_dist * math.sqrt(density))
        sigma_f = max(0.1, sigma_f)

        # Feature vector: [material_idx, defect_type_idx, density]
        features = [mat_map[mat], type_map[dtype], density]
        X_train_list.append(features)
        
        y_train_list["sigma"].append(sigma)
        y_train_list["E"].append(E)
        y_train_list["sigma_f"].append(sigma_f)

    X_train = np.array(X_train_list)
    
    # 2. Train Gaussian Process Surrogates for each target property
    # Kernel: Constant * RBF
    kernel = C(1.0, (1e-3, 1e3)) * RBF(1.0, (1e-2, 1e2))
    
    gp_sigma = GaussianProcessRegressor(kernel=kernel, random_state=seed)
    gp_E = GaussianProcessRegressor(kernel=kernel, random_state=seed)
    gp_sigma_f = GaussianProcessRegressor(kernel=kernel, random_state=seed)
    
    gp_sigma.fit(X_train, y_train_list["sigma"])
    gp_E.fit(X_train, y_train_list["E"])
    gp_sigma_f.fit(X_train, y_train_list["sigma_f"])
    
    # 3. Generate Hold-Out Set using the Surrogates
    # We generate new inputs and predict using the GP (which learned the "Distinct Physics")
    data = []
    for _ in range(n_samples):
        mat = random.choice(materials)
        dtype = random.choice(defect_types)
        density = random.uniform(0.001, 0.1)
        
        features = np.array([[mat_map[mat], type_map[dtype], density]])
        
        # Predict with GP
        pred_sigma, _ = gp_sigma.predict(features)
        pred_E, _ = gp_E.predict(features)
        pred_sigma_f, _ = gp_sigma_f.predict(features)
        
        # Add small noise to emulate measurement/engine uncertainty
        sigma_val = max(0.1, pred_sigma[0] + np.random.normal(0, 0.01 * pred_sigma[0]))
        e_val = max(1.0, pred_E[0] + np.random.normal(0, 0.01 * pred_E[0]))
        sf_val = max(0.1, pred_sigma_f[0] + np.random.normal(0, 0.01 * pred_sigma_f[0]))
        
        entry = {
            "material": mat,
            "defect_type": dtype,
            "defect_density": density,
            "conductivity": sigma_val,
            "elastic_tensor_diag": [e_val, e_val, 0.3*e_val, 0.3*e_val, 0.3*e_val, 0.3*e_val],
            "fracture_energy": sf_val * sf_val / e_val * 10.0,
            "data_source": "gp_surrogate_holdout",
            "version": get_git_hash()
        }
        data.append(entry)
    
    return data

def save_to_csv(data: List[Dict[str, Any]], filepath: Path) -> None:
    """Save data list to CSV file."""
    if not data:
        return
    
    # Ensure directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = list(data[0].keys())
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def run_holdout_generation(output_path: Optional[str] = None) -> str:
    """
    Execute the Hold-Out Mode generation.
    Returns the path to the generated file.
    """
    seed = get_seed()
    n_samples = 50 # Task requirement implies a hold-out set, 50 is reasonable for validation
    
    print(f"[T014] Starting Hold-Out Generation (GP Surrogate) with seed={seed}...")
    
    if output_path is None:
        root = get_project_root()
        output_path = str(root / "data" / "raw" / "synthetic_holdout.csv")
    
    output_file = Path(output_path)
    
    data = generate_holdout_synthetic_data(n_samples=n_samples, seed=seed)
    save_to_csv(data, output_file)
    
    print(f"[T014] Successfully generated {len(data)} hold-out entries to {output_file}")
    return str(output_file)

if __name__ == "__main__":
    run_holdout_generation()
