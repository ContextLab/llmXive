"""
Synthetic Data Generation Module.
Generates ground truth datasets for Inflation and Phase Transition models.

This module creates synthetic CMB B-mode polarization power spectra with known
ground truth parameters (r for inflation, E_PT for phase transitions) and
controlled noise characteristics. These datasets are used to validate the
inference pipeline before processing real observational data.

Requirements:
- r_true = 0.01 for Inflation model
- E_PT_true = 1e15 GeV for Phase Transition model
- Noise level = 1e-5 (Gaussian)
"""
import os
import json
import numpy as np
from typing import Dict, Any, Tuple
import sys
import pathlib

# Add code directory to path if running as script
_code_path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
if _code_path not in sys.path:
    sys.path.insert(0, _code_path)

from model_generation import generate_theoretical_spectrum
from config import get_config, init_reproducibility

def generate_inflation_dataset(
    r_true: float = 0.01,
    noise_level: float = 1e-5,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Generate synthetic inflation dataset with known ground truth.
    
    Args:
        r_true: True tensor-to-scalar ratio (default 0.01 per task spec).
        noise_level: Standard deviation of Gaussian noise.
        seed: Random seed for reproducibility.
    
    Returns:
        Dictionary with l_values, cl_values, noise_variance, model_type, and ground_truth.
    """
    init_reproducibility(seed)
    
    # Multipole range: 2 to 199 (standard for CMB B-mode analysis)
    l_vals = np.arange(2, 200, 1)
    
    # Generate theoretical signal for pure inflation model
    params = {"r": r_true}
    model_type = "inflation"
    
    spec = generate_theoretical_spectrum(model_type, params, l_vals)
    c_true = np.array(spec['cl_values'])
    
    # Add Gaussian noise
    noise = np.random.normal(0, noise_level, size=c_true.shape)
    c_obs = c_true + noise
    
    return {
        "model_type": model_type,
        "params": params,
        "l_values": l_vals.tolist(),
        "cl_values": c_obs.tolist(),
        "noise_variance": (noise_level ** 2) * np.ones_like(c_true).tolist(),
        "ground_truth": {
            "r": r_true,
            "E_PT": None
        },
        "metadata": {
            "noise_level": noise_level,
            "seed": seed,
            "description": "Synthetic inflation dataset with r=0.01"
        }
    }

def generate_phase_transition_dataset(
    E_PT_true: float = 1e15,
    r_true: float = 0.001,
    noise_level: float = 1e-5,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Generate synthetic phase transition dataset with known ground truth.
    
    Args:
        E_PT_true: True energy scale of phase transition in GeV (default 1e15 per task spec).
        r_true: Background tensor-to-scalar ratio from inflation.
        noise_level: Standard deviation of Gaussian noise.
        seed: Random seed for reproducibility.
    
    Returns:
        Dictionary with l_values, cl_values, noise_variance, model_type, and ground_truth.
    """
    init_reproducibility(seed)
    
    # Multipole range: 2 to 199
    l_vals = np.arange(2, 200, 1)
    
    # Generate theoretical signal for phase transition model
    params = {"r": r_true, "E_PT": E_PT_true}
    model_type = "phase_transition"
    
    spec = generate_theoretical_spectrum(model_type, params, l_vals)
    c_true = np.array(spec['cl_values'])
    
    # Add Gaussian noise
    noise = np.random.normal(0, noise_level, size=c_true.shape)
    c_obs = c_true + noise
    
    return {
        "model_type": model_type,
        "params": params,
        "l_values": l_vals.tolist(),
        "cl_values": c_obs.tolist(),
        "noise_variance": (noise_level ** 2) * np.ones_like(c_true).tolist(),
        "ground_truth": {
            "r": r_true,
            "E_PT": E_PT_true
        },
        "metadata": {
            "noise_level": noise_level,
            "seed": seed,
            "description": f"Synthetic phase transition dataset with E_PT={E_PT_true:.0e} GeV"
        }
    }

def save_dataset(data: Dict[str, Any], output_path: str):
    """
    Save dataset to JSON file.
    
    Args:
        data: Dataset dictionary to save.
        output_path: Path to output JSON file.
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    """
    Generate and save synthetic datasets for validation.
    
    Creates two datasets:
    1. Inflation model with r = 0.01
    2. Phase Transition model with E_PT = 1e15 GeV
    
    Both are saved to data/synthetic/ directory.
    """
    # Set seed for reproducibility
    init_reproducibility(42)
    
    output_dir = "data/synthetic"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate and save Inflation dataset (r=0.01)
    print("Generating inflation dataset with r=0.01...")
    data_inf = generate_inflation_dataset(r_true=0.01, noise_level=1e-5, seed=42)
    inflation_path = os.path.join(output_dir, "inflation_r0.01.json")
    save_dataset(data_inf, inflation_path)
    print(f"Saved inflation dataset to {inflation_path}")
    print(f"  Ground truth: r = {data_inf['ground_truth']['r']}")
    print(f"  Multipole range: {data_inf['l_values'][0]} to {data_inf['l_values'][-1]}")
    
    # Generate and save Phase Transition dataset (E_PT=1e15 GeV)
    print("\nGenerating phase transition dataset with E_PT=1e15 GeV...")
    data_pt = generate_phase_transition_dataset(E_PT_true=1e15, r_true=0.001, noise_level=1e-5, seed=42)
    pt_path = os.path.join(output_dir, "phase_transition_E1e15.json")
    save_dataset(data_pt, pt_path)
    print(f"Saved phase transition dataset to {pt_path}")
    print(f"  Ground truth: E_PT = {data_pt['ground_truth']['E_PT']:.0e} GeV")
    print(f"  Ground truth: r = {data_pt['ground_truth']['r']}")
    print(f"  Multipole range: {data_pt['l_values'][0]} to {data_pt['l_values'][-1]}")
    
    print("\nSynthetic data generation complete.")
    print(f"Output directory: {output_dir}")
    print(f"Files created:")
    print(f"  - {os.path.basename(inflation_path)}")
    print(f"  - {os.path.basename(pt_path)}")

if __name__ == "__main__":
    main()