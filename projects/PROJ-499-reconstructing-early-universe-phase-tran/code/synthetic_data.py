import os
import json
import numpy as np
from typing import Dict, Any, Tuple, Optional
import healpy as hp
import sys

from config import get_config, init_reproducibility

# Constants for ground truth
TRUE_R_INF = 0.01
TRUE_E_PT = 1e15  # GeV
TRUE_MODEL_NULL = "null"

def generate_theoretical_BB_spectrum(params: Dict[str, float], l_range: Tuple[int, int] = (2, 200)) -> np.ndarray:
    """
    Generates a theoretical BB power spectrum based on parameters.
    Simplified model for synthetic generation purposes.
    """
    l = np.arange(l_range[0], l_range[1] + 1)
    r = params.get('r', 0.0)
    E_pt = params.get('E_PT', 0.0)
    
    # Tensor contribution (approximate scaling)
    C_l_tensor = r * 1e-10 * (l * (l + 1)) ** -0.5
    
    # Phase transition contribution (approximate peak)
    C_l_pt = 0.0
    if E_pt > 0:
        # Peak around l ~ 100 for high energy scale
        peak_l = 100
        width = 20
        C_l_pt = (E_pt / 1e16)**2 * 1e-10 * np.exp(-0.5 * ((l - peak_l) / width)**2)
    
    # Lensing contribution (Null model baseline)
    # Approximate lensing B-mode spectrum
    C_l_lensing = 2e-10 * (l * (l + 1)) ** -1.5 * (1 - np.exp(-l/5))
    
    C_l_total = C_l_tensor + C_l_pt + C_l_lensing
    return C_l_total

def generate_gaussian_random_field(C_l: np.ndarray, l_range: Tuple[int, int], seed: int) -> np.ndarray:
    """
    Generates a Gaussian random HEALPix map from a given power spectrum.
    """
    nside = 64
    npix = hp.nside2npix(nside)
    map_out = np.zeros(npix)
    
    # Healpix alm generation
    alm = hp.synalm(C_l, l_max=l_range[1], new=True)
    map_out = hp.alm2map(alm, nside, pixwin=False)
    
    return map_out

def generate_inflation_synthetic(output_path: str, seed: int = 42) -> Dict[str, Any]:
    """
    Generates synthetic B-mode maps with inflationary signal (r=0.01).
    """
    init_reproducibility(seed)
    params = {'r': TRUE_R_INF, 'E_PT': 0.0}
    l_range = (2, 200)
    C_l = generate_theoretical_BB_spectrum(params, l_range)
    m_map = generate_gaussian_random_field(C_l, l_range, seed)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    hp.write_map(output_path, m_map, overwrite=True)
    
    return {'model': 'inflation', 'params': params, 'path': output_path}

def generate_pt_synthetic(output_path: str, seed: int = 43) -> Dict[str, Any]:
    """
    Generates synthetic B-mode maps with phase transition signal.
    """
    init_reproducibility(seed)
    params = {'r': 0.0, 'E_PT': TRUE_E_PT}
    l_range = (2, 200)
    C_l = generate_theoretical_BB_spectrum(params, l_range)
    m_map = generate_gaussian_random_field(C_l, l_range, seed)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    hp.write_map(output_path, m_map, overwrite=True)
    
    return {'model': 'phase_transition', 'params': params, 'path': output_path}

def generate_null_synthetic(output_path: str, seed: int = 44) -> Dict[str, Any]:
    """
    Generates synthetic B-mode maps representing the Null (lens-only) model.
    """
    init_reproducibility(seed)
    params = {'r': 0.0, 'E_PT': 0.0}
    l_range = (2, 200)
    C_l = generate_theoretical_BB_spectrum(params, l_range)
    m_map = generate_gaussian_random_field(C_l, l_range, seed)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    hp.write_map(output_path, m_map, overwrite=True)
    
    return {'model': 'null', 'params': params, 'path': output_path}

def serialize_inflation_ground_truth(output_path: str = "data/synthetic/ground_truth_inflation.json") -> None:
    """
    Writes ground truth parameters for inflationary synthetic data to JSON.
    """
    ground_truth = {
        "model_type": "inflation",
        "true_parameters": {
            "r": TRUE_R_INF,
            "E_PT": 0.0
        },
        "description": "Ground truth for T060a synthetic inflation data",
        "seed_used": 42
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(ground_truth, f, indent=2)

def serialize_pt_ground_truth(output_path: str = "data/synthetic/ground_truth_pt.json") -> None:
    """
    Writes ground truth parameters for phase transition synthetic data to JSON.
    """
    ground_truth = {
        "model_type": "phase_transition",
        "true_parameters": {
            "r": 0.0,
            "E_PT": TRUE_E_PT
        },
        "description": "Ground truth for T060c synthetic PT data",
        "seed_used": 43
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(ground_truth, f, indent=2)

def serialize_null_ground_truth(output_path: str = "data/synthetic/ground_truth_null.json") -> None:
    """
    Writes ground truth parameters for null synthetic data to JSON.
    """
    ground_truth = {
        "model_type": "null",
        "true_parameters": {
            "r": 0.0,
            "E_PT": 0.0
        },
        "description": "Ground truth for T060b synthetic null data",
        "seed_used": 44
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(ground_truth, f, indent=2)

def save_dataset(dataset_name: str, data: Any) -> None:
    """Generic dataset saver."""
    pass

def main():
    """Main entry point for synthetic data generation and serialization."""
    print("Generating and serializing synthetic ground truth data...")
    serialize_inflation_ground_truth()
    serialize_pt_ground_truth()
    serialize_null_ground_truth()
    print("Done.")

if __name__ == "__main__":
    main()
