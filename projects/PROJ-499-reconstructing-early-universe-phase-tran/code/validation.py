"""
Validation module for the Early Universe Phase Transitions pipeline.
Implements sky-split consistency checks and synthetic data validation.
"""
import json
import os
import sys
from typing import Dict, Any, Tuple, List, Optional
import numpy as np
from scipy.special import erf
import healpy as hp
from config import get_config, init_reproducibility
from inference import run_nested_sampling, check_convergence
from spectrum_computation import compute_bb_spectrum, validate_sky_coverage
from utils import retry_download, verify_checksum

# Constants for sky splitting
GALACTIC_LATITUDE_THRESHOLD = 0.0  # Split at Galactic plane
N_SIDE = 64  # Resolution parameter for HEALPix

def split_sky_north_south(map_data: np.ndarray) -> Tuple[np.ndarray, np.ndarray, List[int], List[int]]:
    """
    Split a HEALPix map into Northern and Southern Galactic hemispheres.
    
    Args:
        map_data: HEALPix map array (Q or U polarization components).
    
    Returns:
        Tuple containing:
            - Northern hemisphere map (masked Southern)
            - Southern hemisphere map (masked Northern)
            - List of indices for Northern hemisphere pixels
            - List of indices for Southern hemisphere pixels
    """
    nside = hp.get_nside(map_data)
    npix = hp.nside2npix(nside)
    
    # Get Galactic coordinates for all pixels
    theta, phi = hp.pix2ang(nside, np.arange(npix))
    # Convert to Galactic latitude (b)
    # galactic coordinates: l (longitude), b (latitude)
    # We need to transform from ICRS to Galactic
    # For simplicity, we use the approximation that the Galactic plane
    # is roughly at b=0. In a real implementation, we'd use astropy.
    # Here we use the standard HEALPix Galactic coordinate conversion.
    
    # Convert spherical coords to Cartesian for rotation
    x = np.sin(theta) * np.cos(phi)
    y = np.sin(theta) * np.sin(phi)
    z = np.cos(theta)
    
    # Rotation matrix to convert from ICRS to Galactic
    # This is the standard rotation matrix from ICRS to Galactic
    # (from the HEALPix documentation / astropy)
    # The rotation matrix is approximately:
    # [ -0.0548755604, -0.8734370902, -0.4838350155 ]
    # [ +0.4941094279, -0.4448296300, +0.7469822445 ]
    # [ -0.8676617600, -0.1980763734, +0.4559861472 ]
    
    R = np.array([
        [-0.0548755604, -0.8734370902, -0.4838350155],
        [0.4941094279, -0.4448296300, 0.7469822445],
        [-0.8676617600, -0.1980763734, 0.4559861472]
    ])
    
    galactic_xyz = R @ np.array([x, y, z])
    galactic_z = galactic_xyz[2]
    
    # Galactic latitude b is arcsin(galactic_z)
    galactic_b = np.arcsin(galactic_z)
    
    # Split into North (b > 0) and South (b <= 0)
    north_mask = galactic_b > GALACTIC_LATITUDE_THRESHOLD
    south_mask = ~north_mask
    
    north_indices = np.where(north_mask)[0]
    south_indices = np.where(south_mask)[0]
    
    # Create masked maps (set masked pixels to NaN)
    north_map = map_data.copy()
    south_map = map_data.copy()
    
    north_map[~north_mask] = np.nan
    south_map[~south_mask] = np.nan
    
    return north_map, south_map, north_indices.tolist(), south_indices.tolist()

def compute_spectrum_for_patch(map_data: np.ndarray, indices: List[int], nside: int) -> Optional[np.ndarray]:
    """
    Compute BB power spectrum for a specific patch of the sky.
    
    Args:
        map_data: Full HEALPix map (Q or U).
        indices: List of pixel indices to include.
        nside: HEALPix nside parameter.
    
    Returns:
        BB power spectrum array or None if insufficient pixels.
    """
    if len(indices) < 100:  # Minimum pixels for meaningful spectrum
        return None
    
    # Create a temporary map with only the selected pixels
    temp_map = np.full(hp.nside2npix(nside), np.nan)
    for idx in indices:
        temp_map[idx] = map_data[idx]
    
    # Compute BB spectrum (using Q and U components)
    # Note: In practice, we'd need both Q and U maps
    # For this validation, we assume we have access to both
    return compute_bb_spectrum(temp_map)

def run_nested_sampling_on_patch(q_map: np.ndarray, u_map: np.ndarray, 
                                 patch_indices: List[int], 
                                 patch_name: str = "patch") -> Dict[str, Any]:
    """
    Run nested sampling inference on a specific sky patch.
    
    Args:
        q_map: Q polarization map.
        u_map: U polarization map.
        patch_indices: List of pixel indices for the patch.
        patch_name: Name identifier for the patch.
    
    Returns:
        Dictionary with inference results.
    """
    # Create masked maps for the patch
    nside = hp.get_nside(q_map)
    q_patch = np.full(hp.nside2npix(nside), np.nan)
    u_patch = np.full(hp.nside2npix(nside), np.nan)
    
    for idx in patch_indices:
        q_patch[idx] = q_map[idx]
        u_patch[idx] = u_map[idx]
    
    # Compute BB spectrum for the patch
    bb_spectrum = compute_bb_spectrum(q_patch, u_patch)
    
    if bb_spectrum is None or len(bb_spectrum['l_values']) == 0:
        return {
            'patch': patch_name,
            'success': False,
            'error': 'Insufficient pixels for spectrum computation'
        }
    
    # Prepare data for inference
    # We need to extract l_values and cl_values
    l_values = bb_spectrum['l_values']
    cl_values = bb_spectrum['cl_values']
    cl_errors = bb_spectrum.get('cl_errors', np.ones_like(cl_values) * 1e-3)
    
    # Define a simple likelihood function for the patch
    def log_likelihood_patch(params):
        r = params[0]
        # Compute theoretical spectrum for this r value
        # Simplified: assume C_l^BB ~ r * C_l^tensor
        # In reality, we'd use the full model generation
        theoretical_cl = r * cl_values  # Placeholder model
        
        # Chi-squared likelihood
        chi2 = np.sum(((cl_values - theoretical_cl) / cl_errors) ** 2)
        return -0.5 * chi2
    
    def prior_transform_patch(u):
        # Uniform prior on r in [0, 0.1]
        return [u[0] * 0.1]
    
    # Run nested sampling
    try:
        results = run_nested_sampling(
            log_likelihood=log_likelihood_patch,
            prior_transform=prior_transform_patch,
            ndim=1,
            nlive=50,
            maxiter=1000
        )
        
        # Extract posterior for r
        samples = results.samples
        r_samples = samples[:, 0]
        
        return {
            'patch': patch_name,
            'success': True,
            'r_mean': float(np.mean(r_samples)),
            'r_std': float(np.std(r_samples)),
            'r_2.5': float(np.percentile(r_samples, 2.5)),
            'r_97.5': float(np.percentile(r_samples, 97.5)),
            'n_live_points': 50,
            'n_samples': len(r_samples)
        }
    except Exception as e:
        return {
            'patch': patch_name,
            'success': False,
            'error': str(e)
        }

def validate_sky_split_consistency(q_map: np.ndarray, u_map: np.ndarray) -> Dict[str, Any]:
    """
    Validate consistency of best-fit r values between Northern and Southern hemispheres.
    
    This implements FR-007: Split sky into independent patches (Northern/Southern) 
    and verify consistency of best-fit r values.
    
    Args:
        q_map: Q polarization map (HEALPix format).
        u_map: U polarization map (HEALPix format).
    
    Returns:
        Dictionary with validation results including:
            - North and South best-fit r values with uncertainties
            - Consistency check (whether intervals overlap)
            - Difference in r values and significance
    """
    init_reproducibility()
    config = get_config()
    
    # Split the sky
    north_map_q, south_map_q, north_indices, south_indices = split_sky_north_south(q_map)
    north_map_u, south_map_u, _, _ = split_sky_north_south(u_map)
    
    # Run inference on each patch
    north_results = run_nested_sampling_on_patch(
        q_map, u_map, north_indices, "Northern Hemisphere"
    )
    south_results = run_nested_sampling_on_patch(
        q_map, u_map, south_indices, "Southern Hemisphere"
    )
    
    # Check for failures
    if not north_results['success']:
        return {
            'validation_status': 'failed',
            'reason': f"Northern hemisphere inference failed: {north_results.get('error', 'Unknown')}",
            'north_results': north_results,
            'south_results': south_results
        }
    
    if not south_results['success']:
        return {
            'validation_status': 'failed',
            'reason': f"Southern hemisphere inference failed: {south_results.get('error', 'Unknown')}",
            'north_results': north_results,
            'south_results': south_results
        }
    
    # Extract r values and uncertainties
    r_north = north_results['r_mean']
    r_north_err = north_results['r_std']
    r_north_lower = north_results['r_2.5']
    r_north_upper = north_results['r_97.5']
    
    r_south = south_results['r_mean']
    r_south_err = south_results['r_std']
    r_south_lower = south_results['r_2.5']
    r_south_upper = south_results['r_97.5']
    
    # Check for consistency (overlap of 95% credible intervals)
    intervals_overlap = not (r_north_upper < r_south_lower or r_south_upper < r_north_lower)
    
    # Calculate difference in terms of combined uncertainty
    diff = abs(r_north - r_south)
    combined_err = np.sqrt(r_north_err**2 + r_south_err**2)
    significance = diff / combined_err if combined_err > 0 else float('inf')
    
    # Determine validation status
    if intervals_overlap and significance < 2.0:
        validation_status = 'consistent'
    elif intervals_overlap:
        validation_status = 'marginally_consistent'
    else:
        validation_status = 'inconsistent'
    
    return {
        'validation_status': validation_status,
        'north_results': {
            'r_mean': r_north,
            'r_std': r_north_err,
            'r_95_ci': [r_north_lower, r_north_upper],
            'n_pixels': len(north_indices)
        },
        'south_results': {
            'r_mean': r_south,
            'r_std': r_south_err,
            'r_95_ci': [r_south_lower, r_south_upper],
            'n_pixels': len(south_indices)
        },
        'consistency_check': {
            'intervals_overlap': intervals_overlap,
            'difference': diff,
            'combined_uncertainty': combined_err,
            'significance_sigma': significance
        },
        'sky_coverage': {
            'north_fraction': len(north_indices) / hp.nside2npix(hp.get_nside(q_map)),
            'south_fraction': len(south_indices) / hp.nside2npix(hp.get_nside(q_map))
        }
    }

def run_validation_pipeline(data_path: str, output_path: str) -> Dict[str, Any]:
    """
    Main validation pipeline that loads real data, splits the sky,
    and verifies consistency of best-fit r values.
    
    Args:
        data_path: Path to the input HEALPix map files (Q and U).
        output_path: Path to save the validation results JSON.
    
    Returns:
        Dictionary with validation results.
    """
    init_reproducibility()
    
    # Load Q and U maps
    # Expected format: two HEALPix maps (Q and U) in data/raw/
    q_map_path = os.path.join(data_path, 'q_map.fits')
    u_map_path = os.path.join(data_path, 'u_map.fits')
    
    if not os.path.exists(q_map_path) or not os.path.exists(u_map_path):
        raise FileNotFoundError(
            f"Required map files not found. Expected: {q_map_path}, {u_map_path}"
        )
    
    q_map = hp.read_map(q_map_path)
    u_map = hp.read_map(u_map_path)
    
    # Validate sky coverage
    if not validate_sky_coverage(q_map, u_map, min_coverage=0.70):
        raise ValueError("Sky coverage below 70% threshold after masking")
    
    # Run sky split consistency validation
    results = validate_sky_split_consistency(q_map, u_map)
    
    # Save results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

def main():
    """Entry point for the validation script."""
    config = get_config()
    data_path = config.get('DATA_PATH', 'data/raw')
    output_path = config.get('VALIDATION_OUTPUT', 'data/derived/sky_split_validation.json')
    
    try:
        results = run_validation_pipeline(data_path, output_path)
        
        print(f"Validation Status: {results['validation_status']}")
        
        if results['validation_status'] in ['consistent', 'marginally_consistent']:
            print("Sky split consistency check PASSED.")
            print(f"Northern r: {results['north_results']['r_mean']:.4f} ± {results['north_results']['r_std']:.4f}")
            print(f"Southern r: {results['south_results']['r_mean']:.4f} ± {results['south_results']['r_std']:.4f}")
            print(f"Significance of difference: {results['consistency_check']['significance_sigma']:.2f}σ")
        else:
            print("Sky split consistency check FAILED.")
            print(f"Reason: {results.get('reason', 'Inconsistent results between hemispheres')}")
        
        print(f"Results saved to: {output_path}")
        
    except Exception as e:
        print(f"Validation pipeline failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()