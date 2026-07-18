"""
Synthetic data generation for early universe phase transition analysis.

This module provides functions to generate synthetic B-mode polarization maps
based on theoretical models (inflation and phase transitions) for validation
and testing of the inference pipeline.
"""

import os
import json
import numpy as np
from typing import Dict, Any, Tuple
import sys
import pathlib
import healpy as hp

from config import get_config, init_reproducibility

# Ensure reproducibility
init_reproducibility()

def generate_theoretical_BB_spectrum(model_type: str, params: Dict[str, float],
                                     l_max: int = 200) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate a theoretical BB power spectrum for a given model.

    Args:
        model_type: Type of model ('inflation' or 'phase_transition')
        params: Dictionary of model parameters (e.g., {'r': 0.01} or {'E_PT': 1e15})
        l_max: Maximum multipole moment to compute

    Returns:
        Tuple of (l_values, Cl_BB_values)
    """
    l_values = np.arange(2, l_max + 1, dtype=float)
    Cl_BB = np.zeros_like(l_values)

    if model_type == 'inflation':
        r = params.get('r', 0.01)
        # Simplified tensor contribution: ~ r * (l*(l+1))^(-0.5) scaling for demonstration
        # In a real implementation, this would use CAMB or CLASS
        # Using a simplified power law for synthetic data generation
        Cl_BB = r * 1e-10 * (l_values * (l_values + 1)) ** (-0.5)

    elif model_type == 'phase_transition':
        E_PT = params.get('E_PT', 1e15)  # Energy scale in GeV
        # Phase transition signals typically peak at specific scales
        # Using a Gaussian-like bump centered at a characteristic l
        l_peak = 100  # Characteristic scale for phase transitions
        width = 20
        amplitude = (E_PT / 1e16) ** 2 * 1e-9
        Cl_BB = amplitude * np.exp(-0.5 * ((l_values - l_peak) / width) ** 2)

    else:
        raise ValueError(f"Unknown model type: {model_type}")

    return l_values, Cl_BB

def generate_gaussian_random_field(Cl_BB: np.ndarray, l_values: np.ndarray,
                                   nside: int = 64, seed: int = None) -> np.ndarray:
    """
    Generate a Gaussian random B-mode map from a power spectrum.

    Args:
        Cl_BB: Power spectrum values (Cl_BB)
        l_values: Corresponding multipole moments (l)
        nside: HEALPix resolution parameter
        seed: Random seed for reproducibility

    Returns:
        HEALPix map array representing B-mode polarization
    """
    if seed is not None:
        np.random.seed(seed)

    npix = hp.nside2npix(nside)
    map_b = np.zeros(npix)

    # Healpy uses spherical harmonics coefficients a_lm
    # We generate a_lm with the correct power spectrum
    a_lm = hp.synalm(Cl_BB, lmax=len(Cl_BB) - 1, new=True)

    # Generate the map from a_lm
    # We only need the B-mode, so we construct a pure B-mode map
    # For simplicity, we treat the generated a_lm as the B-mode coefficients
    map_b = hp.alm2map(a_lm, nside)

    return map_b

def generate_inflation_synthetic(r_value: float = 0.01, nside: int = 64,
                                 output_dir: str = None, seed: int = 42) -> Dict[str, Any]:
    """
    Generate synthetic B-mode maps for an inflationary model with a given tensor-to-scalar ratio r.

    Args:
        r_value: Tensor-to-scalar ratio (default 0.01)
        nside: HEALPix resolution parameter
        output_dir: Directory to save output files
        seed: Random seed for reproducibility

    Returns:
        Dictionary containing metadata and paths to generated files
    """
    if output_dir is None:
        config = get_config()
        output_dir = config.get('synthetic_data_dir', 'data/synthetic')

    os.makedirs(output_dir, exist_ok=True)

    # Generate theoretical spectrum
    l_values, Cl_BB = generate_theoretical_BB_spectrum('inflation', {'r': r_value})

    # Generate random field
    b_mode_map = generate_gaussian_random_field(Cl_BB, l_values, nside, seed)

    # Prepare ground truth metadata
    ground_truth = {
        'model_type': 'inflation',
        'params': {
            'r': r_value
        },
        'nside': nside,
        'seed': seed,
        'l_values': l_values.tolist(),
        'Cl_BB': Cl_BB.tolist(),
        'description': f'Synthetic B-mode map for inflation with r={r_value}'
    }

    # Save ground truth JSON
    json_path = os.path.join(output_dir, 'ground_truth_inflation.json')
    with open(json_path, 'w') as f:
        json.dump(ground_truth, f, indent=2)

    # Save FITS map
    fits_path = os.path.join(output_dir, 'inflation_synthetic.fits')
    hp.write_map(fits_path, b_mode_map, overwrite=True)

    return {
        'ground_truth_path': json_path,
        'fits_path': fits_path,
        'params': ground_truth['params']
    }

def generate_pt_synthetic(E_PT_value: float = 1e15, nside: int = 64,
                          output_dir: str = None, seed: int = 43) -> Dict[str, Any]:
    """
    Generate synthetic B-mode maps for a phase transition model with a given energy scale E_PT.

    Args:
        E_PT_value: Energy scale of the phase transition in GeV (default 1e15)
        nside: HEALPix resolution parameter
        output_dir: Directory to save output files
        seed: Random seed for reproducibility

    Returns:
        Dictionary containing metadata and paths to generated files
    """
    if output_dir is None:
        config = get_config()
        output_dir = config.get('synthetic_data_dir', 'data/synthetic')

    os.makedirs(output_dir, exist_ok=True)

    # Generate theoretical spectrum
    l_values, Cl_BB = generate_theoretical_BB_spectrum('phase_transition', {'E_PT': E_PT_value})

    # Generate random field
    b_mode_map = generate_gaussian_random_field(Cl_BB, l_values, nside, seed)

    # Prepare ground truth metadata
    ground_truth = {
        'model_type': 'phase_transition',
        'params': {
            'E_PT': E_PT_value
        },
        'nside': nside,
        'seed': seed,
        'l_values': l_values.tolist(),
        'Cl_BB': Cl_BB.tolist(),
        'description': f'Synthetic B-mode map for phase transition with E_PT={E_PT_value} GeV'
    }

    # Save ground truth JSON
    json_path = os.path.join(output_dir, 'ground_truth_pt.json')
    with open(json_path, 'w') as f:
        json.dump(ground_truth, f, indent=2)

    # Save FITS map
    fits_path = os.path.join(output_dir, 'pt_synthetic.fits')
    hp.write_map(fits_path, b_mode_map, overwrite=True)

    return {
        'ground_truth_path': json_path,
        'fits_path': fits_path,
        'params': ground_truth['params']
    }

def save_dataset(dataset_info: Dict[str, Any], output_path: str):
    """
    Save dataset information to a JSON file.

    Args:
        dataset_info: Dictionary containing dataset metadata
        output_path: Path to save the JSON file
    """
    with open(output_path, 'w') as f:
        json.dump(dataset_info, f, indent=2)

def main():
    """Main function to generate synthetic datasets for validation."""
    print("Generating synthetic inflation data...")
    inflation_result = generate_inflation_synthetic(r_value=0.01, seed=42)
    print(f"  Ground truth: {inflation_result['ground_truth_path']}")
    print(f"  FITS map: {inflation_result['fits_path']}")

    print("Generating synthetic phase transition data...")
    pt_result = generate_pt_synthetic(E_PT_value=1e15, seed=43)
    print(f"  Ground truth: {pt_result['ground_truth_path']}")
    print(f"  FITS map: {pt_result['fits_path']}")

    print("Synthetic data generation complete.")

if __name__ == '__main__':
    main()
