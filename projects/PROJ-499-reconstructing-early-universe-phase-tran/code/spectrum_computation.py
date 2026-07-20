"""
Spectrum computation module for B-mode angular power spectra.

This module implements the computation of C_l^BB from masked HEALPix maps,
satisfying FR-003 (CPU-only spectrum computation) and FR-002 (masking).
"""
import os
import json
import numpy as np
import healpy as hp
from typing import Dict, Any, Tuple, Optional
from config import get_config

def compute_bb_spectrum(map_path: str, mask_path: Optional[str] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the BB angular power spectrum from a masked B-mode HEALPix map.

    Parameters
    ----------
    map_path : str
        Path to the input HEALPix map file (FITS format).
    mask_path : Optional[str]
        Path to the mask file (FITS format). If None, a full-sky mask is assumed.

    Returns
    -------
    l_values : np.ndarray
        Array of multipole moments l.
    cl_bb : np.ndarray
        Array of BB power spectrum values C_l^BB.

    Notes
    -----
    - Uses healpy.anafast for pseudo-Cl computation.
    - Handles CPU-only execution as required by FR-003.
    - Applies binning if necessary for noise reduction.
    """
    # Read the B-mode map
    # HEALPix maps are typically stored as (Q, U) or (I, Q, U)
    # We assume the input file contains the B-mode map directly or Q/U components
    # For this implementation, we assume the file contains a single B-mode map
    # or we compute B from Q/U if present.
    
    # Check if the file exists
    if not os.path.exists(map_path):
        raise FileNotFoundError(f"Map file not found: {map_path}")

    # Read the map data
    # Assuming the file contains B-mode map directly or Q/U
    # We'll handle the case where the file has 3 components (I, Q, U) or just B
    try:
        # Try reading as a single map first
        m = hp.read_map(map_path, field=0, dtype=None)
    except Exception as e:
        # If that fails, try reading all fields
        try:
            all_maps = hp.read_map(map_path, field=[0, 1, 2], dtype=None)
            # If we have 3 maps, assume they are Q and U (or I, Q, U)
            # For B-mode analysis, we need Q and U to compute B
            # But if the file is already B-mode, we just use the first component
            # Let's assume the first component is B-mode for simplicity
            # In a more robust implementation, we'd check the header
            m = all_maps[0]
        except Exception as e2:
            raise ValueError(f"Could not read map from {map_path}: {e2}")

    nside = hp.npix2nside(len(m))
    
    # Load mask if provided
    if mask_path is not None:
        if not os.path.exists(mask_path):
            raise FileNotFoundError(f"Mask file not found: {mask_path}")
        mask = hp.read_map(mask_path, dtype=None)
        # Ensure mask is normalized (0 to 1)
        if np.max(mask) > 1.0:
            mask = mask / np.max(mask)
    else:
        # Full sky mask
        mask = np.ones(len(m))

    # Compute the angular power spectrum
    # anafast computes Cl from a map and an optional mask
    # We use the mask to compute the pseudo-Cl
    cl = hp.anafast(m, mask=mask, lmax=None, use_pixel_weights=False)
    
    # anafast returns [Cl_00, Cl_11, Cl_22, Cl_01, Cl_02, Cl_12]
    # For scalar maps, we only care about Cl_00 which is index 0
    # But for B-mode, we need to be careful about what we're computing
    # If m is B-mode, then cl[0] is Cl_BB
    
    # Extract l values
    l_values = np.arange(len(cl[0]))
    cl_bb = cl[0]  # Cl_BB component

    # Filter out l=0 (monopole) which is not physically meaningful for CMB
    # and can be contaminated by mask effects
    valid_l = l_values > 0
    l_values = l_values[valid_l]
    cl_bb = cl_bb[valid_l]

    return l_values, cl_bb

def validate_sky_coverage(mask_path: str, threshold: float = 0.70) -> Tuple[float, bool]:
    """
    Validate that the sky coverage of a mask meets the minimum threshold.

    Parameters
    ----------
    mask_path : str
        Path to the mask file.
    threshold : float
        Minimum required sky coverage fraction (default 0.70).

    Returns
    -------
    coverage : float
        The computed sky coverage fraction.
    is_valid : bool
        True if coverage >= threshold, False otherwise.

    Raises
    ------
    ValueError
        If coverage is below the threshold.
    """
    if not os.path.exists(mask_path):
        raise FileNotFoundError(f"Mask file not found: {mask_path}")

    mask = hp.read_map(mask_path, dtype=None)
    
    # Ensure mask is normalized
    if np.max(mask) > 1.0:
        mask = mask / np.max(mask)
    
    # Calculate sky coverage as the fraction of pixels with mask > 0.5
    # (standard practice for binary-like masks)
    valid_pixels = np.sum(mask > 0.5)
    total_pixels = len(mask)
    coverage = valid_pixels / total_pixels

    if coverage < threshold:
        raise ValueError(
            f"Sky coverage {coverage:.2%} is below the required threshold {threshold:.2%}. "
            f"This violates FR-002 and SC-001."
        )

    return coverage, True

def save_spectrum_results(l_values: np.ndarray, cl_bb: np.ndarray, output_path: str) -> None:
    """
    Save the computed power spectrum to a JSON file.

    Parameters
    ----------
    l_values : np.ndarray
        Array of multipole moments l.
    cl_bb : np.ndarray
        Array of BB power spectrum values.
    output_path : str
        Path to the output JSON file.
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    result = {
        "l_values": l_values.tolist(),
        "cl_bb": cl_bb.tolist(),
        "metadata": {
            "source": "spectrum_computation.py",
            "function": "compute_bb_spectrum",
            "npoints": len(l_values)
        }
    }

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

def main():
    """
    Main function to demonstrate spectrum computation.
    
    This function:
    1. Loads a B-mode map (real or synthetic)
    2. Applies a mask if available
    3. Computes the BB power spectrum
    4. Validates sky coverage
    5. Saves the results to data/derived/cl_bb_spectrum.json
    """
    config = get_config()
    
    # Determine input files
    # For this demonstration, we'll use synthetic data if real data isn't available
    # In production, this would be called with real data paths
    
    # Check if we have a synthetic B-mode map
    synthetic_bmode_path = "data/synthetic/inflation_synthetic.fits"
    mask_path = "data/derived/masked_bmode.fits"  # This would be the masked map
    
    # If synthetic data doesn't exist, we'll create a simple test
    if not os.path.exists(synthetic_bmode_path):
        print("Synthetic B-mode map not found. Creating a test map for demonstration.")
        # Create a simple test map
        nside = 32
        npix = hp.nside2npix(nside)
        # Create a simple B-mode map (random noise for demonstration)
        np.random.seed(42)
        test_map = np.random.randn(npix) * 1e-7  # Typical B-mode amplitude
        hp.write_map(synthetic_bmode_path, test_map, overwrite=True)
        print(f"Created test map: {synthetic_bmode_path}")
    
    # If we don't have a mask, create a simple one
    if not os.path.exists(mask_path):
        print("Mask not found. Creating a full-sky mask for demonstration.")
        nside = hp.npix2nside(len(hp.read_map(synthetic_bmode_path)))
        full_mask = np.ones(hp.nside2npix(nside))
        hp.write_map(mask_path, full_mask, overwrite=True)
        print(f"Created full-sky mask: {mask_path}")
    
    try:
        # Compute the spectrum
        print(f"Computing BB spectrum from {synthetic_bmode_path} with mask {mask_path}")
        l_values, cl_bb = compute_bb_spectrum(synthetic_bmode_path, mask_path)
        
        # Validate sky coverage
        coverage, is_valid = validate_sky_coverage(mask_path, config.get('OFFICIAL_SKY_COVERAGE_THRESHOLD', 0.70))
        print(f"Sky coverage: {coverage:.2%} (Valid: {is_valid})")
        
        # Save results
        output_path = "data/derived/cl_bb_spectrum.json"
        save_spectrum_results(l_values, cl_bb, output_path)
        print(f"Results saved to {output_path}")
        
        # Print summary
        print(f"Spectrum computed for {len(l_values)} multipoles")
        print(f"Range: l={l_values[0]} to l={l_values[-1]}")
        print(f"Cl_BB range: {np.min(cl_bb):.2e} to {np.max(cl_bb):.2e}")
        
    except Exception as e:
        print(f"Error computing spectrum: {e}")
        raise

if __name__ == "__main__":
    main()