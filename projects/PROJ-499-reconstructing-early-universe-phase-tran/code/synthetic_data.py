"""
Synthetic Data Generation Module.
Generates ground truth datasets for Inflation and Phase Transition models.
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
from config import get_config

def generate_inflation_dataset(
    r_true: float,
    noise_level: float = 1e-5,
    include_pt: bool = False,
    E_PT_true: float = 1e15
) -> Dict[str, Any]:
    """
    Generate synthetic inflation dataset with noise.
    
    Args:
        r_true: True tensor-to-scalar ratio.
        noise_level: Standard deviation of Gaussian noise.
        include_pt: Whether to include a Phase Transition signal.
        E_PT_true: True energy scale for PT if included.
    
    Returns:
        Dictionary with l_values, cl_values, noise_variance, model_type.
    """
    l_vals = np.arange(2, 200, 1)
    
    # Generate theoretical signal
    params = {"r": r_true}
    model_type = "inflation"
    
    if include_pt:
        params["E_PT"] = E_PT_true
        model_type = "phase_transition"
    
    spec = generate_theoretical_spectrum(model_type, params, l_vals)
    c_true = np.array(spec['cl_values'])
    
    # Add Gaussian noise
    noise = np.random.normal(0, noise_level, size=c_true.shape)
    c_obs = c_true + noise
    
    # Ensure non-negative (physical constraint, though noise can make it negative)
    # In real data, negative C_l are possible due to noise, but we keep them for likelihood
    
    return {
        "model_type": model_type,
        "params": params,
        "l_values": l_vals.tolist(),
        "cl_values": c_obs.tolist(),
        "noise_variance": (noise_level ** 2) * np.ones_like(c_true).tolist(),
        "ground_truth": {
            "r": r_true,
            "E_PT": E_PT_true if include_pt else None
        }
    }

def generate_phase_transition_dataset(
    E_PT_true: float,
    r_true: float = 0.001,
    noise_level: float = 1e-5
) -> Dict[str, Any]:
    """
    Convenience wrapper for generating PT datasets.
    """
    return generate_inflation_dataset(
        r_true=r_true,
        noise_level=noise_level,
        include_pt=True,
        E_PT_true=E_PT_true
    )

def save_dataset(data: Dict[str, Any], output_path: str):
    """
    Save dataset to JSON.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    """
    Generate and save synthetic datasets.
    """
    output_dir = "data/synthetic"
    os.makedirs(output_dir, exist_ok=True)
    
    # Inflation dataset
    data_inf = generate_inflation_dataset(r_true=0.01, noise_level=1e-5)
    save_dataset(data_inf, os.path.join(output_dir, "inflation_r0.01.json"))
    print(f"Saved inflation dataset to {output_dir}/inflation_r0.01.json")
    
    # Phase Transition dataset
    data_pt = generate_phase_transition_dataset(E_PT_true=1e15, r_true=0.001, noise_level=1e-5)
    save_dataset(data_pt, os.path.join(output_dir, "phase_transition_E1e15.json"))
    print(f"Saved phase transition dataset to {output_dir}/phase_transition_E1e15.json")

if __name__ == "__main__":
    main()
