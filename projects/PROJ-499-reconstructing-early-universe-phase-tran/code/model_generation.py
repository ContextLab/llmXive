"""
Model Generation Module.
Generates theoretical B-mode power spectra for Inflation and Phase Transition models.
"""
import os
import json
import numpy as np
from typing import Dict, Any, List, Tuple

from config import get_config

# Constants
L_MIN = 2
L_MAX = 200
L_STEP = 1

def generate_theoretical_spectrum(
    model_type: str,
    params: Dict[str, float],
    l_vals: np.ndarray
) -> Dict[str, Any]:
    """
    Generate theoretical C_l^{BB} spectrum.
    
    Args:
        model_type: 'inflation' or 'phase_transition'
        params: Dictionary of parameters (e.g., {'r': 0.01} or {'r': 0.001, 'E_PT': 1e15})
        l_vals: Array of multipole moments l.
    
    Returns:
        Dictionary with 'model_type', 'params', 'l_values', 'cl_values'.
    """
    r = params.get('r', 0.0)
    
    # Simple power-law approximation for Inflation B-modes
    # C_l ~ r * A * l^(-2) (very simplified for demonstration)
    # In a real implementation, this would call CAMB/CLASS
    
    # Normalization factor (arbitrary for this synthetic/research context)
    # Based on typical C_l ~ 1e-18 * r at l=10
    A_inflation = 1e-17
    
    cl_values = np.zeros_like(l_vals, dtype=float)
    
    if model_type == 'inflation':
        # C_l ~ r * l^-2
        # Avoid division by zero for l=0 (though l starts at 2)
        mask = l_vals > 0
        cl_values[mask] = r * A_inflation * (l_vals[mask] ** -2)
        
    elif model_type == 'phase_transition':
        E_PT = params.get('E_PT', 1e15)
        # Phase transition signal is peaked at a specific scale
        # Simplified Gaussian peak model
        l_peak = 100 * (E_PT / 1e15) # Scale with energy
        width = 20
        
        # Amplitude scales with (E_PT / M_pl)^4 roughly, simplified here
        amp = (E_PT / 1e16) ** 4 * 1e-16
        
        # Add inflation component if r is non-zero
        if r > 0:
            mask = l_vals > 0
            cl_values[mask] += r * A_inflation * (l_vals[mask] ** -2)
        
        # Add PT component
        cl_values += amp * np.exp(-0.5 * ((l_vals - l_peak) / width) ** 2)
        
    else:
        raise ValueError(f"Unknown model_type: {model_type}")

    return {
        "model_type": model_type,
        "params": params,
        "l_values": l_vals.tolist(),
        "cl_values": cl_values.tolist()
    }

def main():
    """
    Generate a grid of models and save to JSON.
    """
    config = get_config()
    l_range = np.arange(L_MIN, L_MAX, L_STEP)
    
    models = []
    
    # Grid for Inflation: r over a relevant small-range interval
    # Using log spacing for better coverage of small r values
    r_grid = np.logspace(-4, -1, 5) # 0.0001, 0.001, 0.01, 0.1, 1.0 (clamped to reasonable)
    r_grid = [0.0001, 0.001, 0.01, 0.05, 0.1]
    
    for r in r_grid:
        spec = generate_theoretical_spectrum("inflation", {"r": float(r)}, l_range)
        models.append(spec)
    
    # Grid for Phase Transition: E_PT in [10^14, 10^16] GeV (log scale)
    E_grid = np.logspace(14, 16, 5) # 1e14, 1e14.5, 1e15, 1e15.5, 1e16
    
    for E in E_grid:
        # Include a small inflation component for realism
        spec = generate_theoretical_spectrum("phase_transition", {"r": 0.001, "E_PT": float(E)}, l_range)
        models.append(spec)
    
    output_path = "data/derived/theoretical_spectra.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(models, f, indent=2)
    
    print(f"Generated {len(models)} theoretical spectra saved to {output_path}")

if __name__ == "__main__":
    main()